def to_category(male_prob: float, age_years: float, th_male: float, age_cut: float) -> str:
    male   = male_prob >= th_male
    senior = age_years  >= age_cut
    if male and not senior: return "young_male"
    if (not male) and not senior: return "young_female"
    if male and senior: return "senior_male"
    return "senior_female"
