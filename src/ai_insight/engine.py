# /home/pi/Kiosk_ai/src/ai_insight/engine.py
import numpy as np
import insightface

class InsightfaceEngine:
    """
    - FaceAnalysis 한 번 호출로 탐지 + 속성(age, gender)까지 얻어
      파이프라인이 기대하는 형식으로 반환하는 어댑터.
    - 반환 형식:
        detect(frame) -> [(x1,y1,x2,y2,score), ...]
        attrs_for_largest(frame) -> (best_box, attrs, boxes_all)
          attrs = {"male_prob": float, "age_years": float}
    """
    def __init__(self,
                 providers=("DmlExecutionProvider", "CPUExecutionProvider"),
                 det_size=(320, 320),
                 male_prob_hard=0.9):
        # 사용 가능한 provider만 채택
        try:
            avail = set(insightface.model_zoo.get_available_providers())
        except Exception:
            avail = set()
        use = [p for p in providers if p in avail] or ["CPUExecutionProvider"]

        self.app = insightface.app.FaceAnalysis(providers=use)
        # CPU 고정(ctx_id=-1). det_size는 속도/정확도 트레이드오프
        self.app.prepare(ctx_id=-1, det_size=det_size)

        # insightface는 성별을 0(여)/1(남)로만 줌 → 파이프라인 male_prob 필요해서 매핑
        self.male_prob_pos = float(male_prob_hard)
        self.male_prob_neg = float(1.0 - self.male_prob_pos)

    @staticmethod
    def _to_box(face):
        # (x1,y1,x2,y2,score)
        x1, y1, x2, y2 = face.bbox.astype(np.int32).tolist()
        sc = float(getattr(face, "det_score", 1.0))
        return (x1, y1, x2, y2, sc)

    def detect(self, frame):
        faces = self.app.get(frame) or []
        return [self._to_box(f) for f in faces]

    def infer_attrs_from_face(self, face):
        # 0=Female, 1=Male
        if int(getattr(face, "gender", 0)) == 1:
            male_prob = self.male_prob_pos   # ex) 0.9
        else:
            male_prob = self.male_prob_neg   # ex) 0.1
        return {"male_prob": float(male_prob), "age_years": float(getattr(face, "age", 30.0))}

    def attrs_for_largest(self, frame):
        faces = self.app.get(frame) or []
        if not faces:
            return None, None, []
        faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)
        best = faces[0]
        box = self._to_box(best)
        attrs = self.infer_attrs_from_face(best)
        boxes_all = [self._to_box(f) for f in faces]
        return box, attrs, boxes_all
