<!-- omit in toc -->
# Contributing to Unified Planning Library

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Post on it on social networks
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->
## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
- [Join The Project Team](#join-the-project-team)


## Code of Conduct

This project and everyone participating in it is governed by the
[Unified Planning Library Code of Conduct](https://github.com/aiplan4eu/unified-planningblob/master/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <unified-planning-maintainers@googlegroups.com>.


## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://unified-planning.readthedocs.io/en/latest/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/aiplan4eu/unified-planning/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/aiplan4eu/unified-planning/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (python version, operating system, ...), depending on what seems relevant.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree to the [Developer Certificate of Origin (DCO)](DCO.txt): all commits must be signed-off with your real name to signal the adherence to the DCO legal statement.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://unified-planning.readthedocs.io/en/latest/). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/aiplan4eu/unified-planningissues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
  - Possibly your input and the output
  - Can you reliably reproduce the issue? And can you also reproduce it with older versions?

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/aiplan4eu/unified-planning/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as possibly other tags (such as `critical`), and the issue will be left to be [implemented by someone](#your-first-code-contribution).


### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Unified Planning Library, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://unified-planning.readthedocs.io/en/latest/) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/aiplan4eu/unified-planning/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/aiplan4eu/unified-planning/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- **Explain why this enhancement would be useful** to most Unified Planning Library users. You may also want to point out the other projects that solved it better and which could serve as inspiration.


### Code Contribution

Before start coding, open an issue or a discussion on the project [GitHub space]((https://github.com/aiplan4eu/unified-planning) or get in contact with a maintainer (you can use the project mailing list: unified-planning@googlegroups.com)! It is possible that someone else is already working on the same or a related fix or feature!

Moreover, we have to keep a reasonable project scope, so if your contribution is wildly beyond the current capabilities of the library, it is better to discuss the idea with the community and the maintainers to avoid unpleasant situations where we have to reject your code.

When contributing new code to the library, you have to follow the development practices both in terms of code style and practices (Static checks, type annotations, unit testing and continuous integration). Again, get in contact with a maintainer and frequently push your code on a Pull-Request (in draft mode) so that the community can give you early feedback and support.

Remember to sign-off (https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---signoff) every commit to signal your acceptance of the [Developer Certificate of Origin](/DCO.txt).


### Improving The Documentation

We warmly welcome improvements to our documentation (which is kept alongside the code in the main repository). Both stylistic/grammatical fixes and new content are welcome contribution, but please make sure to maintain a professional tone and ensure that the information you provide in the docs is accurate and up-to-date with the current development branch.


## Join The Project Team

Everyone is welcome to contribute to join our project! Have a look at the [GOVERNANCE.md](/GOVERNANCE.md) file to understand the project roles and the governance mechanism we established.

In order to become a Contributor, please get in contact with a Maintainer: we are happy to give direct writing access to the project repository to simplify the development of frequent contributors.

Maintainers are selected by the Board of Maintainers from active Contributors, but you can ask the current maintainers to be evaluated by sending a (private) email to the Board of Maintainers mailing list (unified-planning-maintainers@googlegroups.com).

<!-- omit in toc -->
## Attribution
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
