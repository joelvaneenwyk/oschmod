# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

## Bug Reports

When [reporting a bug][issues] please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

## Documentation Improvements

_oschmod_ could always use more documentation, whether as part of the official
_oschmod_ docs, in docstrings, or even on the web in blog posts, articles, and
such. The official documentation is maintained within this project in
docstrings or in the [docs][documentation] directory. Contributions are
welcome, and are made the same way as any other code.

## Feature Requests and Feedback

The best way to send feedback is to [file an issue][issues] on GitHub.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a community-driven, open-source project, and that
  code contributions are welcome. :)

## Development Guide

To set up _oschmod_ for local development:

1. Fork [_oschmod_](https://github.com/yakdriver/oschmod) (look for the
   "Fork" button).

2. Clone your fork locally:

   ```bash
   git clone https://github.com/your_name_here/oschmod.git && cd oschmod
   ```

3. Create a branch for local development:

   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```

4. Now you can make your changes locally.

5. When you're done making changes, use Make to run the linters, the tests,
   and the doc builder. (WIP)

6. Commit your changes and push your branch to GitHub:

   ```bash
   git add .
   git commit -m "Your detailed description of your changes."
   git push origin name-of-your-bugfix-or-feature
   ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

If you need some code review or feedback while you are developing the code just
open the pull request.

For pull request acceptance, you should:

1. Make sure CI (e.g., GitHub Actions) are successful
2. Update documentation whenever making changes to the API or functionality.
3. Add a note to `CHANGELOG.md` about the changes. Include a link to the
   pull request.

[issues]: https://github.com/yakdriver/oschmod/issues
[documentation]: https://github.com/joelvaneenwyk/oschmod/issues
