<!-- omit in toc -->
# Governance of the Unified Planning Library

This documents describes the governance bodies and procedures ruling the development of the Unified Planning library. The purpose of crystallizing such roles and procedures is to make the governance process and the decisions as transparent as possible and to set a clear path for external contributions in the decision making process.


<!-- omit in toc -->
## Table of Contents

- [History](#history)
- [General Governance Spirit](#general-governance-spirit)
- [Roles](#roles)
- [Communication Channels](#communication-channels)
- [Technical Rules](#technical-rules)
- [Membership Rules](#membership-rules)


# History

The UP library has been initiated within the AIPlan4EU project and was initially developed and designed by Fondazione Bruno Kessler (Andrea Micheli, Alessandro Valentini and Luca Framba) as technical leader of the associated work-package in the AIPlan4EU project, with contributions (mostly in terms of feedback and discussions) from other AIPlan4EU project partners.

Subsequently, the library received significant contributions from LAAS-CNRS (Arthur Bit-Monnot), the University of Brescia (Alberto Rovetta) and the University of Rome "La Sapienza" (Alessandro Trapasso).

Up to June 30th 2023, the development of the library has been coordinated by Andrea Micheli (in the role of work-package leader in the AIPlan4EU project), discussing with the AIPlan4EU project partners the technical and design choices in a bi-weekly remote meeting.

Starting from July 1st 2023, the UP project is ruled according to the prescriptions in this document.


# General Governance Spirit

The UP project wants to implement a ["do-ocracy"](https://www.redhat.com/en/blog/understanding-open-source-governance-models): people actively contributing to the development should be the ones allowed to make the decisions.

This general principle will apply from the technical level (e.g. by determining who can accept or reject external contributions and have the commit permissions) to the strategic level (e.g. by determining who can decide if a certain feature needs to be developed or is out of scope).

This document describes a lightweight set of procedures designed to implement this general spirit as effortlessly as possible for the stakeholder involved.


# Roles

We only recognize two roles in the UP project:

- **Committer**: a person who can create new branches and commit on any branch except the "master" branch;
- **Maintainer**: a Committer who can also commit on the "master" branch. A list of all active Maintainers is always kept up-to-date in the [MAINTAINERS](/MAINTAINERS) file.

In addition, being an open source project we welcome external contributions coming from external forks of the UP project. We will refer to such Pull-Requests as "External Contributions".

The **Board of Maintainers** is the main decision body of the UP project and is composed of all the current Maintainers.


# Communication Channels

We establish two official communication channels for the UP project.

- The **Maintainers Mailing List** (unified-planning-maintainers@googlegroups.com): all and only the active Maintainers are part of this list. The mailing list is not publicly readable but anyone can send messages to it. It is the main and official communication channel among maintainers and to communicate to the board of maintainers.

- The **Public Mailing List** (unified-planning@googlegroups.com): is a general-purpose communication channel to be used for both technical matters and public announcements. the list is publicly readable and anyone can join it. All decisions and votes of the Board of Maintainers are publicly communicated through this list.

On these channels, as well as in any other virtual space associated with the library, the code of conduct of the UP project applies.


# Technical Rules

The following rules apply for the technical day-to-day governance of the project.

- Any Maintainer can approve and commit to "master" a Pull-Request from any Committer, External Contribution or **another** Maintainer.

- It is forbidden to anyone to self-approve and commit a Pull-Request.

- It is mandatory for any commit pushed to master (after June 30th 2023) to be signed off to signal the acceptance of the Developer Certificate of Origin (DCO) rules.

- It is forbidden to anyone to modify this document, unless **all** the Maintainers approve the Pull-Request.

- Any Maintainer can make new releases (on GitHub and PyPI) of the UP library (taking the code of the "master" branch) autonomously, but must inform all the other Maintainers and Committers through the public mailing list.

- Only a full consensus vote (meaning that all the Maintainers agree, with no abstentions) of the Board of Maintainers can change the name, web address or digital identity of the UP project.


# Membership Rules

The following rules govern the promotion and demotion of Committers and Maintainers.

- Any Maintainer can autonomously nominate (and give the needed permissions) any number of Committers. (The rationale is that being a Committer does not grant any specific power over the project, but simplifies the work for people who often contribute to the library).

- Any Maintainer can step down (effective immediately) from being a Maintainer by informing the Board of Maintainers.

- Only a majority vote of the Board of Maintainers can nominate new Maintainers. The number rof Maintainers is not fixed.

- Only a full consensus vote (meaning that all the Maintainers agree, with no abstentions) of the Board of Maintainers can modify the governance rules layed out in this document.

- In order to remove an Maintainer unwilling to leave his/her position, a 75% majority vote of the other Maintainers is needed.



