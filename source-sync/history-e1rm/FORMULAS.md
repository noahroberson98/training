# Formulas and the pages that were opened

These are estimates from a logged weight and a rep count. They are not a measured one-rep max, not a clinical test, and not a suggestion to attempt a max. The log does not say whether a set was taken to failure.

## Epley, primary

`estimated 1RM = weight * (1 + reps / 30)` for a whole rep count of 2 or more.

Opened: [One-repetition maximum](https://en.wikipedia.org/wiki/One-repetition_maximum), which lists Epley as `w * (1 + r / 30)` and cites Boyd Epley, "Poundage Chart", *Boyd Epley Workout*, Lincoln, NE: Body Enterprises, 1985, p. 86. The same page says indirect estimates can miss a measured max by 10% or more, that the common formulas diverge after about 10 reps, and that Epley and Brzycki match at 10 reps. Its worked example matches the code: 100 lb for 10 reps is about 133 lb either way; 100 lb for 6 reps is about 120 lb by Epley and about 116 lb by Brzycki.

Opened: LeSuer, McCormick, Mayhew, Wasserstein, and Arnold, "The Accuracy of Prediction Equations for Estimating 1-RM Performance in the Bench Press, Squat, and Deadlift", *Journal of Strength and Conditioning Research* 11(4):211–213, 1997. PDF: https://paulogentil.com/pdf/The%20Accuracy%20of%20Prediction%20Equations%20for%20Estimating%201-RM%20Performance%20in%20the%20Bench%20Press,%20Squat,%20and%20Deadlift.pdf . DOI: https://doi.org/10.1519/00124278-199711000-00001 . Their Table 1 writes Epley as `(1 + .0333 × reps) × rep wt`, which is the same relationship as dividing by 30. They tested repetitions to fatigue of 10 or fewer in 67 untrained college students. Correlations were above 0.95, and the equations still had significant average error. Every equation they tested underestimated the deadlift. Bench press predictions were closer than squat, which were closer than deadlift. They also cite Brzycki that fewer than 10 reps to fatigue were better for an estimate.

## Brzycki, comparison only

`comparison = weight * 36 / (37 - reps)` for whole reps from 2 through 10. That is the same as `weight / (1.0278 - 0.0278 × reps)`.

Opened: Matt Brzycki, "Strength Testing—Predicting a One-Rep Max from Reps-to-Fatigue", *Journal of Physical Education, Recreation & Dance* 64(1):88–90, January 1993. PDF: https://brzycki.scholar.princeton.edu/sites/g/files/toruqf4561/files/brzycki/files/mb-1993-01.pdf . DOI: https://doi.org/10.1080/07303084.1993.10606684 . Figure 1 prints `Predicted 1-RM = Weight / (1.0278 - .0278 X)`. The article says the relationship is not quite linear beyond about 10 reps, and that the formula is only valid when reps-to-fatigue are less than 10. Above about 10 reps it says the test is less accurate for the estimate. Table 1 includes a 10-rep column and, at 1 rep, prints the load itself (100 lb for 1 rep is 100). The article also says a reps-to-fatigue test is not a direct measure of maximal strength, and that people differ in how many reps they can do at a given percent of max.

The chart draws Brzycki as its own dashed series. It is never copied onto the Epley line, so the two methods cannot switch and create a spike. At 10 reps the two formulas meet, so the 10-rep point is not a method switch. Brzycki is not called above 10 reps, which also avoids a zero or negative denominator (`37 - reps`).

## A logged single

A set of exactly 1 rep is shown as that weight. Epley would multiply it by `31/30` (about 3.3%). That bump is not in the log, and Brzycki's own table is the load at 1 rep, so both displayed methods agree. The label says it is the logged single, not a verified max: the log does not say the single was a maximal effort.

## Rep limits

- 2–10: Epley on the solid line, Brzycki as the dashed comparison.
- 11–12: Epley only. Not flagged low confidence. Brzycki is omitted because the 1993 article limits the linear formula to under about 10 reps.
- Above 12: Epley is still computed, marked low confidence, drawn as an open point, and not connected to the solid estimate line. LeSuer's subjects stopped at 10 reps. The chart uses 12 as the flag the request asked for, which is past the range those papers actually tested.
- The session's best estimate prefers a 1–12 rep set over an above-12 set. An above-12 set is the session estimate only when nothing else in that unit is eligible.

## What this does not claim

The number is not a lab 1RM. It is not equally accurate for every exercise. LeSuer's deadlift errors were about 9–14% even with high correlations. It is not advice to load a bar to the estimate.
