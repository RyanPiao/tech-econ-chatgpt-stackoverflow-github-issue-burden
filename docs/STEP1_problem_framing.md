# Step 1 — Problem Framing

## Topic
**ChatGPT and the shift from Stack Overflow to GitHub issue burden**

## Core causal question
After ChatGPT’s public launch on November 30, 2022, did software ecosystems that were more reliant on Stack Overflow before the launch experience a larger increase in GitHub issue burden?

## Variables
- **Outcome variable:** monthly GitHub issue burden, measured with issue-open counts, issue-open duration, and time-to-close metrics for selected public repositories
- **Treatment variable:** the interaction of the post-ChatGPT period with a pre-period measure of Stack Overflow dependence

## Unit of analysis
- Ecosystem-month or repository-group-month panels, depending on data quality and mapping feasibility
- Candidate ecosystems include major public language and framework communities with active Stack Overflow tagging and public GitHub issue histories

## Why this matters
Open-source software communities rely on support channels that are costly to maintain. Stack Overflow historically absorbed a large share of routine troubleshooting and knowledge exchange, while GitHub issues were better suited for project-specific bugs, feature requests, and maintenance discussion. If generative AI reduced question posting on public Q&A sites, the effect might not be a pure productivity gain: some support demand may simply have been redirected toward maintainers and issue trackers.

That matters for platform economics, open-source labor, and digital public goods. A visible drop in Stack Overflow activity could reflect improved self-service, but it could also hide a transfer of unpaid support work onto maintainers, especially in ecosystems that previously depended heavily on forum-based troubleshooting.

## Framing and empirical direction
The leading empirical design is a panel difference-in-differences or event-study setup. The comparison would ask whether ecosystems with higher pre-2022 Stack Overflow dependence saw larger post-launch changes in GitHub issue burden relative to ecosystems that depended less on Stack Overflow before ChatGPT became widely available.

A practical first estimand is the change in monthly issue-open counts or average issue-open duration after the launch, scaled by a pre-period Stack Overflow dependence measure. The core interpretation would remain cautious: this design is best suited to detecting substitution patterns in support channels, not to claiming that ChatGPT directly caused all observed changes in maintainer workload.

## Data strategy (public real data)
1. **Stack Overflow / Stack Exchange side**
   - Public monthly question counts, tag activity, and related forum-volume measures from Stack Exchange public data access routes such as BigQuery, the public data dump, or Data Explorer.
   - These data can be used to construct a pre-period dependence score for ecosystems or tags.
2. **GitHub side**
   - Public issue events from GH Archive and repository metadata from GitHub’s public APIs.
   - Candidate outcomes include issue-open counts, comment intensity, closure timing, and unresolved backlog measures.
3. **Intervention timing**
   - Post period anchored to ChatGPT’s public launch on **2022-11-30**.

## Assumptions challenged
1. **Lower Stack Overflow activity automatically means lower support demand.** Some support work may have moved to maintainers, Discord servers, GitHub issues, or direct AI usage instead.
2. **GitHub issue counts cleanly measure support burden.** Issue trackers also capture bugs, feature requests, and roadmap coordination, not just displaced Q&A.
3. **Pre-period Stack Overflow dependence is stable and meaningful.** Ecosystems differ in documentation culture, chat usage, and repository governance.
4. **Post-2022 changes are unique to ChatGPT.** Broader shifts in open-source activity, funding conditions, layoffs, or repository migration could also move issue volumes.

## Key risks
- **Mapping risk:** linking Stack Overflow tags to representative GitHub repositories or ecosystem groupings may be noisy.
- **Measurement risk:** issue activity may mix support burden with true product development work.
- **Confounding risk:** post-2022 platform and labor-market shocks may overlap with the AI shock.
- **Interpretation risk:** a measured increase in GitHub issue activity does not by itself prove harmful overload; it could also reflect healthier project engagement.

## Recommendation
Proceed with a tightly scoped Step 2 build using a manageable set of ecosystems with strong public data availability and clear tag-to-repository mappings. The topic is well suited to a public GitHub workflow because the data path is real, the causal question is timely and intelligible, and the final result can speak to a broad audience interested in AI, open-source labor, and digital platform substitution.