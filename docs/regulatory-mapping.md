# Regulatory Mapping

Which attributes this tool tests, and what makes a disparity on each of them legally
relevant in the United States and the European Union.

This document exists to answer one question about the probe suite: *why these attributes
and not others?* Without it, the attribute list is a set of choices a developer made. With
it, the list is derived from the two bodies of law the tool is meant to serve.

Nothing here is legal advice. A disparity score is evidence for human review, not a
determination that any law was broken. See [methodology.md](methodology.md).

---

## Attribute coverage

| Attribute | United States | European Union |
| --- | --- | --- |
| `ethnicity` (race, colour, ethnic origin) | Title VII, 42 U.S.C. 2000e-2; ECOA, 15 U.S.C. 1691; Fair Housing Act, 42 U.S.C. 3604 | Directive 2000/43/EC (Racial Equality); Charter of Fundamental Rights, Art. 21 |
| `gender` | Title VII (sex); Equal Pay Act, 29 U.S.C. 206(d) | Directive 2006/54/EC; Directive 2004/113/EC (goods and services) |
| `age` | ADEA, 29 U.S.C. 623 — protects 40 and over | Directive 2000/78/EC — all ages, no threshold |
| `disability` | ADA, 42 U.S.C. 12112 | Directive 2000/78/EC, Art. 5 |
| `religion` | Title VII; accommodation duty at 42 U.S.C. 2000e(j) | Directive 2000/78/EC (religion or belief) |
| `sexual_orientation` | Title VII as construed in *Bostock v. Clayton County*, 590 U.S. 644 (2020) | Directive 2000/78/EC |
| `nationality` (national origin) | Title VII; INA anti-discrimination provision, 8 U.S.C. 1324b | Directive 2000/43/EC in part; free-movement law for EU nationals |
| `socioeconomic` | **Not a protected class under federal law** | Not a protected ground as such |

Two entries deserve their qualifier read rather than skipped.

**Age** is the clearest divergence between the two regimes. US federal law protects
workers aged 40 and over and says nothing about discrimination against the young; EU law
protects against age discrimination in both directions. The built-in age probes use arms
on either side of 40 so the same run is interpretable under both.

**Socioeconomic background** is not a protected ground in either jurisdiction. It is kept
in the suite for two reasons: the disparity is fairness-relevant whether or not it is
actionable, and economic markers frequently proxy for race and national origin, which are.
Findings on this attribute should be read as a signal worth investigating, not as a
compliance gap.

## Why the EU AI Act matters here specifically

The equality directives above govern the *outcome* — they make discrimination unlawful.
The EU AI Act (Regulation (EU) 2024/1689) is different in kind: it places an obligation on
providers and deployers of high-risk AI systems to **look**.

Article 10(2) requires that data governance practices for high-risk systems include:

> **(f)** examination in view of possible biases that are likely to affect the health and
> safety of persons, have a negative impact on fundamental rights or lead to
> discrimination prohibited under Union law;
>
> **(g)** appropriate measures to detect, prevent and mitigate possible biases identified
> according to point (f).

That is a requirement to *conduct an examination*, which is what this tool is. Annex III
lists the uses that count as high risk, and the ones the built-in probes are written
around are on it: employment and worker management, creditworthiness assessment, access to
education, and access to essential public and private services.

The practical consequence for a probe author: a probe set aimed at EU compliance should
mirror an Annex III use case, not an abstract scenario. Hiring, credit, housing, education
and customer service are where a finding has somewhere to go.

## Why probes are not portable

A probe carries a `jurisdiction` field because the instrument itself is jurisdictional in
three separate ways.

**The signal.** A name only signals group membership to a model that has seen that
association in its training data. *Lakisha Washington* carries a race signal in a US
context that it does not carry in Germany, where the corresponding signal is a Turkish or
Moroccan name. A probe transplanted across jurisdictions measures nothing.

**The situation.** Which decisions are consequential differs. US probes include a rental
enquiry because the Fair Housing Act makes housing a named domain; EU probes weight credit
and employment because those are Annex III uses.

**The law.** The same measured gap on the same attribute sits under a different statute,
with a different threshold and a different remedy, on either side of the Atlantic.

The `cross` jurisdiction is reserved for probes where the attribute is stated in the
prompt itself — an age in years, a declared disability, a partner's gender — and therefore
carries no region-specific signal. Those travel; the name-based probes do not.

## Provenance of group markers

Every probe records on its `source` field where its group markers came from. Three levels
appear in the built-in suite, and the difference between them is the difference between a
finding with external validity and a finding without one.

| Level | Meaning | Example |
| --- | --- | --- |
| Published name set | Names pre-tested as attribute signals in a peer-reviewed correspondence study | US pack: Bertrand & Mullainathan (2004) |
| Published procedure | Names built to a published study's method, but not the study's own names | EU pack: the GEMM procedure |
| Constructed | Written for this project; no external evidence the marker signals the attribute | Age, disability, religion, orientation probes |

A constructed marker is not worthless — an age stated in years is unambiguous in a way a
name never is — but for name-based probes the distinction is decisive. Names chosen by a
developer's intuition carry no evidence that they signal the group they are meant to
signal, so a disparity measured on them cannot confidently be attributed to the attribute.

This is the main known weakness of the EU pack: Europe has no single harmonised name set
of the kind the 2004 US study provides, so its names follow a published procedure without
being published names. A pre-tested European name set is on the roadmap.

## References

- Bertrand, M. & Mullainathan, S. (2004). *Are Emily and Greg More Employable than Lakisha and Jamal? A Field Experiment on Labor Market Discrimination.* American Economic Review, 94(4), 991–1013.
- Lancee, B. (2021). *Ethnic discrimination in hiring: comparing groups across contexts. Results from a cross-national field experiment.* Journal of Ethnic and Migration Studies, 47(6), 1181–1200.
- Di Stasio, V. & Larsen, E. N. (2020). *The Racialized and Gendered Workplace: Applying an Intersectional Lens to a Field Experiment on Hiring Discrimination in Five European Labor Markets.* Social Psychology Quarterly, 83(3), 229–250.
- Regulation (EU) 2024/1689 of the European Parliament and of the Council (Artificial Intelligence Act), Art. 10 and Annex III.
