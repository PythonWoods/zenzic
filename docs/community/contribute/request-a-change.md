---
icon: lucide/hand-platter
tags:
  - Community
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change requests {#change-requests}

Zenzic is a powerful documentation linting tool. We aim to support a wide range
of use cases, and change requests are an essential mechanism for ensuring that
our software meets the needs of our community.

!!! warning "How we manage change requests"

    We highly value every idea or contribution from our community, and we
    kindly ask you to take the time to read the following guidelines before
    submitting your change request in our public [issue tracker]. Before
    submitting a new idea, please take a moment to read
    [how we manage change requests].

  [issue tracker]: https://github.com/PythonWoods/zenzic/issues

## Before creating an issue

Before you invest your time filling out a change request, please answer the
following preliminary questions to determine if your idea is a good fit for
Zenzic.

### It's not a bug, it's a feature

Change requests are intended to suggest minor adjustments, propose ideas for
new features, or provide input to the project's direction. They are **not**
intended for reporting bugs — please refer to our [bug reporting guide] instead.

  [bug reporting guide]: report-a-bug.md

### Look for sources of inspiration

If you have seen your idea implemented in another tool, gather enough
information about its implementation before submitting, as this will help us
evaluate potential fit more quickly.

**Keep track of all <u>search terms</u> and <u>relevant links</u>, you'll need
them in the change request.**

## Issue template

Our change request template consists of the following parts:

- [Title]
- [Context] <small>optional</small>
- [Description]
- [Related links]
- [Use cases]
- [Visuals] <small>optional</small>
- [Checklist]

  [Title]: #title
  [Context]: #context
  [Description]: #description
  [Related links]: #related-links
  [Use cases]: #use-cases
  [Visuals]: #visuals
  [Checklist]: #checklist

### Title

A good title is short and descriptive — a one-sentence executive summary of
the idea, so the potential impact and benefit can be inferred at a glance.

### Context <small>optional</small> { #context }

Provide additional context to help us understand what you are trying to achieve.
Don't write about the change request here.

> **Why this might be helpful**: some ideas might only benefit specific settings
> or edge cases. Context helps us prioritize more accurately.

### Description

Provide a detailed and precise description of your idea. Explain why it is
relevant to Zenzic specifically.

- **Explain the <u>what</u>, not the <u>why</u>** – focus on describing the
    proposed change precisely. Benefits belong in [Use cases].

- **Keep it short** – be brief and to the point.

- **One idea at a time** – open separate change requests for unrelated ideas.

### Related links

Provide relevant links to issues or documentation sections related to your
change request, including any prior community discussions.

### Use cases

Explain how your change request would work from an author's and user's
perspective — what's the expected impact, who will benefit, and would it
potentially break existing functionality?

### Visuals <small>optional</small> { #visuals }

If you have sketches, screenshots, mockups, or examples from other tools, share
them here. You can drag and drop files into the text area or include links.

### Checklist

Thanks for following the guide and creating a high-quality change request. The
checklist ensures that you have read this guide and provided us with every piece
of information to review your idea.

**We'll take it from here.**

---

## How we manage change requests

Change requests are submitted as issues on our public [issue tracker]. Here's
how we handle them:

1. We read and review the request to understand the idea.
2. We may leave comments to clarify intent or suggest alternatives.
3. If the idea is out of scope, we will close the request and explain why.
4. If the idea aligns with the project's vision, we'll move it to our backlog.
5. Otherwise, we close the request to keep the issue tracker focused on bugs.

## Rejected requests

**Your change request got rejected? We're sorry for that.** We understand it
can be frustrating, but as maintainers we always need to consider the needs of
our entire community.

The following principles (in no particular order) form the basis for our
decisions:

- [ ] Alignment with the vision and goals of the project
- [ ] Compatibility with existing features
- [ ] Effort of implementation and maintenance
- [ ] Usefulness to the majority of users
- [ ] Simplicity and ease of use

If you're unsure why your change request was rejected, please don't hesitate
to ask for clarification.
