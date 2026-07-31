# Human Eval Current Summary

Files: human_eval_sheet_1.csv, human_eval_sheet_2.csv
Rows: review1=100, review2=100; common valid rows=99
Invalid rows: {'review1': [], 'review2': ['H078']}
Text/output differences: ['H078']

## review1
Valid rows: 100 (invalid: [])
Bokmal model: adequacy=1.930, Bokmal conformity=1.920
Original-sub model: adequacy=1.910, Bokmal conformity=0.940
Delta Bokmal - Original-sub: adequacy=+0.020, Bokmal conformity=+0.980
Preference counts: {'bokmal': 59, 'tie': 25, 'original_subsampled': 16}; sign-test p=6.11416e-07
control: n=50, pref={'tie': 25, 'original_subsampled': 16, 'bokmal': 9}, delta adequacy=+0.000, delta Bokmal=+0.040, p=0.229523
shift: n=50, pref={'bokmal': 50}, delta adequacy=+0.040, delta Bokmal=+1.920, p=1.77636e-15

## review2
Valid rows: 99 (invalid: ['H078'])
Bokmal model: adequacy=1.909, Bokmal conformity=1.828
Original-sub model: adequacy=1.899, Bokmal conformity=1.040
Delta Bokmal - Original-sub: adequacy=+0.010, Bokmal conformity=+0.788
Preference counts: {'bokmal': 55, 'tie': 33, 'original_subsampled': 11}; sign-test p=3.60145e-08
control: n=49, pref={'tie': 31, 'bokmal': 10, 'original_subsampled': 8}, delta adequacy=-0.041, delta Bokmal=-0.020, p=0.814529
shift: n=50, pref={'bokmal': 45, 'original_subsampled': 3, 'tie': 2}, delta adequacy=+0.060, delta Bokmal=+1.580, p=1.31259e-10

## Inter-reviewer agreement on 99 common valid rows
adequacy_a_0_1_2: exact=98.0%, kappa=0.823
adequacy_b_0_1_2: exact=92.9%, kappa=0.631
bokmal_a_0_1_2: exact=89.9%, kappa=0.796
bokmal_b_0_1_2: exact=85.9%, kappa=0.718
preference_model_winner: exact=85.9%, kappa=0.751