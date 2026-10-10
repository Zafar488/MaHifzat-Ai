# Reference basis and interpretation

- [WHO antenatal care contact schedule](https://www.who.int/news-room/detail/07-11-2016-pregnant-women-must-be-able-to-access-the-right-care-at-the-right-time-says-who): contact milestones are 12, 20, 26, 30, 34, 36, 38 and 40 weeks. The application uses these as scheduling prompts and prioritizes a supplied clinician appointment. Local schedules and individual care plans can differ.
- [NICE hypertension in pregnancy](https://www.nice.org.uk/guidance/ng133/chapter/recommendations): severe blood pressure and headache/visual symptoms inform escalation prompts.
- [WHO pregnancy/childbirth care guide](https://www.ncbi.nlm.nih.gov/books/NBK326676/): rapid danger-sign assessment informs emergency escalation. The rules are conservative prompts for clinician review, not an exhaustive diagnostic engine.
- [UCI Maternal Health Risk](https://archive.ics.uci.edu/dataset/863/maternal+health+risk) and [UCI Cardiotocography](https://archive.ics.uci.edu/dataset/193/cardiotocography): model targets reflect these datasets' labels and feature contracts. CTG features must use the documented units; absent CTG is not assessed.

The project reports internal experimental label performance. No local clinical validation, treatment recommendation or guaranteed referral acceptance is inferred from these sources.
