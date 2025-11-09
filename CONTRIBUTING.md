# Contributing

Thanks for your interest in contributing to this project! Small contributions and improvements are welcome. Please follow these simple guidelines to make the review process fast and effective.

1. Fork the repository and create a feature branch from `main` (or `master`) named using this pattern:

   - `feature/<short-description>` for new features
   - `fix/<short-description>` for bug fixes

2. Keep changes small and focussed. Open an issue first for larger changes and discuss the approach.

3. Code style and tests

   - Use sensible, readable code. For Python, prefer idiomatic style (PEP8). Running `black` and `flake8` locally is encouraged.
   - If you add code, add a small test or a usage example where feasible.

4. Commit messages and PRs

   - Use clear commit messages. One-line summary + optional body is preferred.
   - Open a pull request against `main` with a concise description of the change and any manual test instructions.

5. Keep secrets out of commits

   - Never commit real credentials. Use `.env` files and local copies of `wokwi/secrets.py` for development. The repository `.gitignore` already excludes these files.

6. License

   - By contributing you agree that your contribution will be licensed under the project's license (see `LICENSE`).

If you need help, open an issue describing what you'd like to do and tag it `help wanted`.

Thanks — maintainers
