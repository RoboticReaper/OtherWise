# OtherWise discovery

OtherWise aims to broaden the topics people come to care about. Its discovery goal is user-tunable; the default uses unfamiliar but connected suggestions to spark curiosity and support new interests. Immediate appeal helps start exploration, while sustained interest expansion is the intended outcome.

## Language

**Interest phrase**:
Text a person supplies to describe an interest. A phrase can refer to more than one meaning and does not establish what the person already knows.
_Avoid_: Known topic

**Topic sense**:
A particular meaning of an interest phrase, such as Java the programming language or Java the island. Matching words alone does not establish a matching sense.

**Catalog topic**:
A named subject available for broad exploration, with a description that identifies its intended meaning. A catalog is a collection of available subjects, not a complete vocabulary.
_Avoid_: Word list

**Discovery concept**:
A specific, identifiable idea available to explore, with a description and a source. One concept can belong to several subject areas.

**Learning opportunity**:
A specific phenomenon, method, strategy, question, or mechanism a person could explore. Familiarity with its parent field does not establish familiarity with this particular idea. A generated explanation retains the underlying source identity.

**Source path**:
An observed chain of category memberships connecting a discovery concept to a subject area. A source path does not establish a learning prerequisite or the person's reason for being interested.

**Connectedness**:
A meaningful relationship between a suggestion and one or more of the person's interests. Semantic similarity is evidence to investigate, not proof that the person recognizes the connection.

**Familiarity**:
How much the person already knows about a suggested concept. Distance from an interest is a modeling assumption, not a measurement of familiarity.

**Curiosity**:
The person's desire to explore a suggestion. Curiosity can coexist with familiarity or difficulty.

**Interest expansion**:
Growth in the distinct topics a person chooses to keep exploring beyond their previous interests. Record newly adopted interests and their retention, and distinguish added depth within a field from breadth across subject areas. Exposure, clicks, knowledge gains and embedding distance alone do not establish that someone has come to care about a topic. A previously familiar topic can become a new interest.

**Proxy interestingness**:
A recommendation's score under a declared automated rubric. It supports comparisons for specific objectives without claiming to measure the person's actual curiosity.

## Future human research

On 2026-10-08, the user agreed to blind comparisons plus controlled variants for formal human-participant research. Formalizing the experimental design is deferred to a new chat; the present discussion concerns feasible options and candidate systems, rather than building an experiment.

The saved [study research and candidate notes](docs/recommendation-human-study-research.md) record the accepted direction, proposed systems/baselines, sources and unresolved design choices. Candidate selection remains a proposal. Automated score leaders and the private single-participant preference check do not establish a general human-study winner, an exploration rate or an interest-expansion effect.

On 2026-10-08, the user clarified that broadening the topics people care about is the primary mission. Future evaluation should measure retained new-interest acquisition and breadth, with curiosity and preference as intermediate outcomes. The user subsequently authorized implementing all discussed candidates/baselines, including trajectory-guided expansion, and specified optional `date` on each interest. The [selectable backend models](docs/recommendation-model-api.md) include static K/V candidates, simple baselines and a matched `history-recency`/`trajectory` pair. Direction estimates use dated semantic strands and an explicit fallback; execution tests do not establish an expansion effect. Raw lab V0 is preserved; its API wrapper has versioned meaning/known-output guards. Formalizing the metrics and study remains deferred.
