# AI tooling guide

This project provides repository-specific instructions for GitHub Copilot in
`.github/copilot-instructions.md`. The file gives AI coding tools the project architecture,
privacy constraints, branch policy, coding conventions, and validation commands.

## How to use it

1. Open this repository in a Copilot-enabled editor or on GitHub.
2. Check out the appropriate feature branch before requesting changes.
3. Describe one concrete task and identify whether it affects the RAG pipeline, backend,
   or React frontend.
4. Ask Copilot to run the validation commands listed in the instruction file.
5. Review the diff and commit it with a descriptive message.

Example request:

> On `feature/frontend-chat-ui`, add a copy-answer control to the message component.
> Preserve the existing design, keyboard accessibility, and local-only behavior. Run the
> frontend production build and summarize the changed files.

AI-generated code is a starting point, not an automatic approval. A developer should
review grounding behavior, data handling, dependency changes, and test results before
committing or opening a pull request.
