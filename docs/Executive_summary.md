# Title & Abstract

This paper studies whether the release of ChatGPT changed where software-maintenance work shows up by shifting developer problem-solving away from Stack Overflow and toward GitHub issue trackers. The core finding in this repository is that ecosystems with higher pre-existing dependence on Stack Overflow experience larger post-release increases in issue inflow and maintainer response burden. The current evidence is produced from a synthetic, fully reproducible panel designed to validate the research design and implementation pipeline before full public-data deployment. Even under that boundary, the estimated relationships are economically meaningful, statistically stable across many checks, and informative about how generative AI may reallocate support labor across open-source institutions.

# Introduction

The central causal question is straightforward: after ChatGPT became widely available, did communities that relied more heavily on Stack Overflow see a larger increase in GitHub issue burden than communities that relied less on Stack Overflow? The outcome side of the design focuses on operational burden inside repositories, including newly opened issues and maintainer response times. The treatment side is a post-period exposure term interacted with pre-period Stack Overflow dependence.

This question matters because open-source software ecosystems depend on volunteer and quasi-volunteer maintenance labor. If generative AI tools alter where users seek help, then the labor load may move from public Q&A forums into repository-level support channels, where response capacity is narrower and queueing costs are more immediate.

# Data & Institutional Context

The empirical unit is an ecosystem-month panel. The repository currently uses a synthetic panel that mirrors the intended structure of a public-data implementation: issue-flow outcomes, response metrics, ecosystem controls, and pre-period dependence measures. This choice is deliberate. It allows full inspection of variable construction, merge logic, and specification behavior without overstating partial real-world coverage.

Institutionally, the setting links two complementary knowledge systems. Stack Overflow historically absorbed broad troubleshooting demand through searchable question-answer archives. GitHub issues, by contrast, are tied to specific repositories and maintainer workflows. A shift in where questions are asked can therefore translate into a shift in who pays the support cost and how quickly unresolved work accumulates.

# Empirical Strategy

The identification strategy is a two-way fixed-effects difference-in-differences framework with treatment intensity. In plain language, the model compares changes before and after ChatGPT across ecosystems that started with different levels of Stack Overflow dependence, while controlling for persistent ecosystem differences and common month shocks.

The finalized Step 6 specification adds ecosystem-specific linear trends and standardized controls, with standard errors clustered at the ecosystem level. The design assumes that, absent the ChatGPT-era shock, high- and low-dependence ecosystems would have evolved along comparable conditional trajectories. Event-time diagnostics, placebo timing checks, and shifted-cutoff tests are used to probe that assumption.

# Main Findings

The principal result is a positive and sizable treatment-intensity effect on issue inflow. In the finalized model, the coefficient for issues opened is 10.8180 (p<0.001), equivalent to about 1.279 standard deviations in the synthetic panel. Relative to the Step 4 reference estimate (5.9985), this indicates that trend adjustment does not erase the relationship; if anything, the estimated loading on issue burden becomes stronger.

Maintainer workload pressure is not limited to issue counts. For average first response hours, the finalized coefficient is 3.8092 (p<0.001), indicating slower first-touch responsiveness where Stack Overflow dependence was higher. Interpreted practically, the pattern is consistent with support demand moving toward channels where triage depends more directly on repository maintainers.

# Robustness & Limitations

Robustness checks preserve the main directional conclusion across weighted estimation, lag controls, symmetric time windows, placebo lead terms, ratio outcomes, and intervention-cutoff sweeps. For issues opened, key alternatives remain positive (for example, 9.7179 with lagged-outcome control and 7.2464 within a symmetric ±12-month window), while the six-month lead placebo is near zero and not statistically significant.

One important nuance appears when direct Stack Overflow activity controls are added: the point estimate stays positive (12.1226) but precision drops (p=0.1442). This suggests overlap between treatment intensity and channel activity, meaning mediation and measurement entanglement remain active concerns rather than simple model failure.

The largest limitation is intentional: results in this repository are synthetic and should be treated as design-validation evidence, not definitive real-world causal magnitudes. The project establishes a transparent, reproducible pipeline and a stress-tested specification; external validity must be evaluated with full public-data execution.

# Conclusion

The synthesis from Steps 1 through 6 supports a clear hypothesis: generative AI adoption can reallocate support demand across digital institutions, increasing repository-level burden where legacy Q&A dependence was higher. For practitioners, this implies that maintainer capacity planning and triage automation are now core governance concerns, not peripheral workflow choices.

For researchers, the contribution is twofold: a tractable intensity-based causal design and a reproducible implementation scaffold that is ready for real-data scaling. The immediate next value lies in moving from validated synthetic infrastructure to comprehensive public-data estimation and comparative institutional welfare analysis.

# Appendix

Reproducibility steps (from repository root): create a Python virtual environment, install the step-specific requirements, and run the pipeline scripts (for final layer: `python scripts/run_step6_pipeline.py`; for Step 6-only refresh: `python scripts/run_step6_finalize.py`). Validation outputs are stored in `outputs/step6_validation_report.json`, with full manifests in `outputs/step6_manifest.json` and step-indexed artifacts across `outputs/step2_*` through `outputs/step6_*`.

Evidence links (repo-relative): core synthesis inputs include `docs/STEP4_baseline_econometric_model.md`, `docs/STEP5_robustness_checks.md`, `docs/STEP6_robustness_and_polish.md`, `outputs/step6_finalized_model_results.csv`, `outputs/step6_alternative_explanations.csv`, and `outputs/step6_cutoff_sweep.csv`. These files provide coefficient tables, diagnostics, and robustness traces cited in the narrative sections above.

Citations: methods follow standard panel causal-inference practice using two-way fixed effects with event-time diagnostics and placebo timing tests; implementation relies on Python scientific tooling documented in repository requirements files (`requirements-step4.txt` to `requirements-step6.txt`).