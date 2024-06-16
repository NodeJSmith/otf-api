# Changelog

All notable changes to this project will be documented in this file. See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

## [unreleased]

[7e2ff79](7e2ff79f640f90b78959af038a07305749091f8f)...[]()

### Other (unconventional)

- Remove conditional check for push event with tags in python_package.yml ([07699fe](https://github.com/nodejsmith/otf-api/commit/07699fe00d12102cea332f895347baad5270bf7b)) - @


## [0.1.1] - 2024-06-15

[b7f8f91](b7f8f9197679c9095aadd4f2a5ea4bba56e35ef2)...[7e2ff79](7e2ff79f640f90b78959af038a07305749091f8f)

### Other (unconventional)

- Merge pull request #10 from NodeJSmith/cleanup/more_cleanup

Cleanup/more cleanup ([f6f244b](https://github.com/nodejsmith/otf-api/commit/f6f244be1492481a09045484a2c2f8168f1fd831)) - @NodeJSmith

- Ci(workflows): update python_package workflow to separate build and publish steps
ci(workflows): add test_and_lint workflow for testing and linting on push and PR events
 ([253abe2](https://github.com/nodejsmith/otf-api/commit/253abe223da239dd7609c893d7eb060005d6abe0)) - @NodeJSmith

- Remove publishing of build artifacts from test/lint workflow ([23f1392](https://github.com/nodejsmith/otf-api/commit/23f1392e5a063f408e4684e18ee5170920052c6d)) - @NodeJSmith

- Rename workflow from 'Python package' to 'Test and Lint' for clarity ([730f8eb](https://github.com/nodejsmith/otf-api/commit/730f8eb27d503a95b33d8dc5ad297424efded0df)) - @NodeJSmith

- Remove dev build CI workflow file ([eafa7d5](https://github.com/nodejsmith/otf-api/commit/eafa7d52ebd3dc6a7b7d86a84007c278d3cf6fce)) - @NodeJSmith

- Merge pull request #11 from NodeJSmith/feature/releasing

Feature/releasing ([7e2ff79](https://github.com/nodejsmith/otf-api/commit/7e2ff79f640f90b78959af038a07305749091f8f)) - @NodeJSmith


## [0.1.0] - 2024-06-15

### Bug Fixes

- Change cr_waitlist_flag_last_updated type from str to datetime for accuracy ([4310693](https://github.com/nodejsmith/otf-api/commit/4310693e4f8c135bb7a60e1d196e6cf84f1f788f)) - @NodeJSmith

- Change type of cr_waitlist_flag_last_updated from str to datetime for accuracy ([086370f](https://github.com/nodejsmith/otf-api/commit/086370fae472f12fe420e6500edbbbb3773ab11e)) - @NodeJSmith

- Change type of cr_waitlist_flag_last_updated from str to datetime for accurate representation of date/time values ([18e80d0](https://github.com/nodejsmith/otf-api/commit/18e80d0a405ba7c11326b8b174ae540e8a63eec9)) - @NodeJSmith

- Fix pyproject, get tox working, add first test
 ([287a53e](https://github.com/nodejsmith/otf-api/commit/287a53e5957b8a6377c0f23cacba94332f75be10)) - @NodeJSmith

- Fix mypy errors
 ([e654e2e](https://github.com/nodejsmith/otf-api/commit/e654e2e6ee985cc254e9a86ec3e9d44d2a25d8cb)) - @NodeJSmith

- Fix tox
 ([a37e4c6](https://github.com/nodejsmith/otf-api/commit/a37e4c6fdc025ef8a4fcadf57890f0307ae709fe)) - @NodeJSmith

- Fix docstrings for griffe
 ([764e61c](https://github.com/nodejsmith/otf-api/commit/764e61c4a4624aebfc06e1cf8cd39f28d4639b66)) - @NodeJSmith

- Fix extra - should be docs, not doc
 ([992b6ff](https://github.com/nodejsmith/otf-api/commit/992b6ff7b78a7de16f05a0372fa5d55d395c476f)) - @NodeJSmith

- Fix(tox.ini): replace poetry with pipx in deps to manage dependencies
feat(tox.ini): add pipx install poetry in commands_pre to ensure poetry is installed
 ([eefb5b3](https://github.com/nodejsmith/otf-api/commit/eefb5b3320f658550b0c7a353fda2ecdc8dbb059)) - @NodeJSmith

- Add poetry install command to ensure dev dependencies are installed before running checks ([3f6957f](https://github.com/nodejsmith/otf-api/commit/3f6957f7cb2cdaa5dbea703d84d39cc64f786b30)) - @NodeJSmith

- Fix reference to dna
 ([2b6443c](https://github.com/nodejsmith/otf-api/commit/2b6443c7dfdee96b7bcbc889c13b6f207a98e647)) - @NodeJSmith


### Documentation

- Docs
 ([5c23abf](https://github.com/nodejsmith/otf-api/commit/5c23abfd05671ba3780eb8f6312260a0cb37b55f)) - @NodeJSmith

- Docstrings, make some members private
 ([0263298](https://github.com/nodejsmith/otf-api/commit/02632986a3c74dcffe5c2b33e32ca2f46d065eed)) - @NodeJSmith

- Correct typos in package download URLs in dev and release workflows ([a60c055](https://github.com/nodejsmith/otf-api/commit/a60c05507b7cd75e0377042e6898c883f368e2f5)) - @NodeJSmith

- Docs(CONTRIBUTING.md): update reference from HISTORY.md to CHANGELOG.md
docs: rename history.md to changelog.md and update references
 ([d6ca531](https://github.com/nodejsmith/otf-api/commit/d6ca531d9617f9d99ef08ce60f8943051b15b485)) - @NodeJSmith


### Features

- Add literal_eval import and use for parsing HR data ([c2b2899](https://github.com/nodejsmith/otf-api/commit/c2b28990a55ef5c3d6c574d2eb176154a445c06b)) - @NodeJSmith

- Enhance header handling in API requests to allow custom headers ([11e42eb](https://github.com/nodejsmith/otf-api/commit/11e42ebec0a076014e8eddebd80f67c773cf3597)) - @NodeJSmith

- Feat(api.py): enforce username and password as required for Api class
feat(api.py): add class method to create Api instance with user details
docs(api.py): update constructor docstring to explain username and password necessity
feat(api.py): introduce member home studio and timezone attributes in Api class
 ([def9aca](https://github.com/nodejsmith/otf-api/commit/def9aca25bc3001ab897f63b9f74df410839b610)) - @NodeJSmith

- Integrate PerformanceApi for performance data handling ([020d6d5](https://github.com/nodejsmith/otf-api/commit/020d6d5a9e2d961fc57e6427101aacaf8f835dad)) - @NodeJSmith

- Introduce OtfBaseModel with model_config for shared configuration ([70781b6](https://github.com/nodejsmith/otf-api/commit/70781b6f0e63cce1ebaa69024d97adc5d947572f)) - @NodeJSmith


### Miscellaneous Chores

- Pin dependencies to specific versions for consistent builds ([656e3ab](https://github.com/nodejsmith/otf-api/commit/656e3ab4bf7464a54d317347bd2262bca23e5689)) - @NodeJSmith

- Chore(pyproject.toml): add pre-commit and mypy to dev dependencies for code quality
chore(pyproject.toml): pin versions for mkdocs and related plugins to ensure compatibility
 ([a4fadbf](https://github.com/nodejsmith/otf-api/commit/a4fadbf9364b016d0e98660f13eb809eccdf3861)) - @NodeJSmith

- Chore(tox.ini): remove skipsdist option to enable source distribution
chore(tox.ini): add allowlist_externals for lint and build environments
chore(tox.ini): update allowlist_externals in default testenv
chore(tox.ini): add commands_pre to ensure dependencies are installed
chore(tox.ini): update pytest command to use importlib import mode
 ([c09ee88](https://github.com/nodejsmith/otf-api/commit/c09ee8825ecaaf1ea28ed7b2737c724e8d93fdc8)) - @NodeJSmith

- Add commands_pre section with echo to ensure pre-commands run before main commands ([a6acddd](https://github.com/nodejsmith/otf-api/commit/a6acddd54a44144512d52fb1fcf39404b8ba7df7)) - @NodeJSmith

- Chore(tox.ini): replace echo with comment symbol in commands_pre to clean up configuration
chore(tox.ini): update allowlist_externals to include only necessary tools poetry and pipx
 ([b76a5ce](https://github.com/nodejsmith/otf-api/commit/b76a5ce650825bd7f028b0437aa3d15e33fe0f99)) - @NodeJSmith

- Chore(pre-commit): add mypy and commitizen hooks to pre-commit config
refactor(telemetry): replace TelemetryItem with Telemetry in telemetry API
fix(models): update imports and __all__ to reflect Telemetry changes
feat(models): add Telemetry model to handle telemetry data
 ([63feb5f](https://github.com/nodejsmith/otf-api/commit/63feb5f9109a5af06f5716a2aab011e0fa3b755c)) - @NodeJSmith

- Remove commitizen hook configuration to streamline pre-commit checks ([c439a79](https://github.com/nodejsmith/otf-api/commit/c439a791d1de42bdb59847895240fb9f8ffe4ac8)) - @NodeJSmith

- Add git-cliff configuration file for automated changelog generation ([190e05f](https://github.com/nodejsmith/otf-api/commit/190e05f1fcec1662c048e6e1bb0f846a5895f75f)) - @NodeJSmith

- Generate changelog ([14abcb7](https://github.com/nodejsmith/otf-api/commit/14abcb747f82587ca94490a9a5dea667d74f636f)) - @NodeJSmith

- Update changelog ([446fdf1](https://github.com/nodejsmith/otf-api/commit/446fdf12b2daccfc6339425850c4a00bd2c266c6)) - @NodeJSmith

- Chore: add .codespellrc configuration file to define codespell settings
chore: update .pre-commit-config.yaml to include codespell hook and update ruff to v0.4.9
 ([eba311c](https://github.com/nodejsmith/otf-api/commit/eba311c393edb0c5249c5d0aad8053116011b86b)) - @NodeJSmith

- Chore(deps): update ruff from 0.4.8 to 0.4.9
feat(deps): add httpx version 0.27.0 for HTTP requests
 ([b7f8f91](https://github.com/nodejsmith/otf-api/commit/b7f8f9197679c9095aadd4f2a5ea4bba56e35ef2)) - @NodeJSmith


### Other (unconventional)

- Initial commit
 ([1a86683](https://github.com/nodejsmith/otf-api/commit/1a86683da24e1b462183310f28476dbe3c5a211f)) - @NodeJSmith

- Add scratch to gitignore
 ([41ff851](https://github.com/nodejsmith/otf-api/commit/41ff8514f7379e9094ac01d8f20c27e5c4a5346d)) - @NodeJSmith

- Add _get_bookings_old for documentation, add more notes to get_bookings
 ([87ee9db](https://github.com/nodejsmith/otf-api/commit/87ee9db5ee0087f3ec539ef27fd0a63fbe8209a4)) - @NodeJSmith

- Make class optional
 ([ec46e3c](https://github.com/nodejsmith/otf-api/commit/ec46e3ca981ec308cf0f04bf55b81d0a597b6e5a)) - @NodeJSmith

- Add all_statuses to HistoryBookingStatus
 ([5111ddb](https://github.com/nodejsmith/otf-api/commit/5111ddbbe5bc06d5ec750b707af36139986f3e83)) - @NodeJSmith

- Add new files, update pyproject
 ([70e9df5](https://github.com/nodejsmith/otf-api/commit/70e9df5a0295ef562d12204dfbdf0da80739c02b)) - @NodeJSmith

- Add tox.ini and github workflow
 ([c11da57](https://github.com/nodejsmith/otf-api/commit/c11da575e26472a4c8922fb6e0b5f9045cfd6e73)) - @NodeJSmith

- Update action
 ([d441aaf](https://github.com/nodejsmith/otf-api/commit/d441aaf8d6fd7e3bb72b5bce3890405ccc6518b2)) - @NodeJSmith

- Add cache pip
 ([6122ca6](https://github.com/nodejsmith/otf-api/commit/6122ca6f1836cedd689b6cf7cc2f8a8a8d27fc1a)) - @NodeJSmith

- Add python version to cache keys
 ([d074c68](https://github.com/nodejsmith/otf-api/commit/d074c68f2e67e772c4dc974826a3518e5c0c61fe)) - @NodeJSmith

- Update to node 20
 ([78535fe](https://github.com/nodejsmith/otf-api/commit/78535fe3af3681d4b3cfe6b94b8e9a0ffc51c8cd)) - @NodeJSmith

- Merge pull request #1 from NodeJSmith/feature/add_perf_summary_api

Feature/add perf summary api - lots of improvements, not just performance summary. not bothering with bump since not published yet ([34836ff](https://github.com/nodejsmith/otf-api/commit/34836fffef2059e56dc84f5d2ddc5508ad98a51b)) - @NodeJSmith

- Start adding md files, docs, tests, etc
 ([3caca8b](https://github.com/nodejsmith/otf-api/commit/3caca8b687f6012ec2ac6259ae051b5faee946bc)) - @NodeJSmith

- More docs stuff
 ([4666c71](https://github.com/nodejsmith/otf-api/commit/4666c719ac886d67044e56ec8bcd8114ee654d7e)) - @NodeJSmith

- Merge pull request #2 from NodeJSmith/feature/make_user_friendly

feature/make user friendly ([3ae7dcf](https://github.com/nodejsmith/otf-api/commit/3ae7dcfb267582332698e61ce9d406d701222178)) - @NodeJSmith

- Renaming everything to oft-api
 ([8906eaa](https://github.com/nodejsmith/otf-api/commit/8906eaa9db791b46d7f7e170aac686d04013131a)) - @NodeJSmith

- Add examples and add more to usage page
 ([6b38dad](https://github.com/nodejsmith/otf-api/commit/6b38dad346db995d02eb3ef7d72dc2d8b0fda4e9)) - @NodeJSmith

- Correct location
 ([6ab8a0e](https://github.com/nodejsmith/otf-api/commit/6ab8a0e472c27c44ff222e476ad9c1ece2fbe052)) - @NodeJSmith

- Create dependabot.yml ([acb8574](https://github.com/nodejsmith/otf-api/commit/acb8574d668a8b08e17e8ea783a4eb862419296f)) - @NodeJSmith

- Update action to run test and lint separate
 ([61ef2df](https://github.com/nodejsmith/otf-api/commit/61ef2df24f8771eb7d0610d49124863889b7f436)) - @NodeJSmith

- Add verbose flags to tox
 ([c9ce530](https://github.com/nodejsmith/otf-api/commit/c9ce53053133b16d27b86005771604237c4501f6)) - @NodeJSmith

- Add mkdocs build step directly
 ([3701fe5](https://github.com/nodejsmith/otf-api/commit/3701fe55fa92993611997d22089e1958a9e1c017)) - @NodeJSmith

- Install dev and docs deps first, comment out other steps for now
 ([c1ddf17](https://github.com/nodejsmith/otf-api/commit/c1ddf1786393f2ec600aee3150283c50a45d3186)) - @NodeJSmith

- Tweak tox.ini
 ([a08de7a](https://github.com/nodejsmith/otf-api/commit/a08de7a1548c2916b46ba3d571764a2cc9e3899c)) - @NodeJSmith

- Add env
 ([a302519](https://github.com/nodejsmith/otf-api/commit/a302519a8b9b08b50ec5c0225d18a2ec85cc7c36)) - @NodeJSmith

- Use matrix version when running tox
 ([e77dd54](https://github.com/nodejsmith/otf-api/commit/e77dd54ef80d9a62527f307061f52fc80df3a12c)) - @NodeJSmith

- Merge pull request #6 from NodeJSmith/fix/tox

Fix tox lint stage ([9e64811](https://github.com/nodejsmith/otf-api/commit/9e648114482b593471d8313b68d44b6d6ff44461)) - @NodeJSmith

- Switch to poetry to simplify tox
 ([732192d](https://github.com/nodejsmith/otf-api/commit/732192d700d31ab09720815e40a8f70410af54bd)) - @NodeJSmith

- Add build checks to GitHub Actions workflow to ensure package builds correctly ([c5a2afe](https://github.com/nodejsmith/otf-api/commit/c5a2afe7f2686416144e2e2424cec8e4f7e4f3b4)) - @NodeJSmith

- Increase verbosity of tox commands to improve debugging and output clarity ([cf44695](https://github.com/nodejsmith/otf-api/commit/cf4469535d760335cdd8d8d20bcab6c6cfa4070e)) - @NodeJSmith

- Remove verbose flag from tox commands to reduce log output ([bbf91e6](https://github.com/nodejsmith/otf-api/commit/bbf91e656abeca9daf09fbb8d30a607717004694)) - @NodeJSmith

- Add mkdocs build step to GitHub Actions workflow ([cad2af2](https://github.com/nodejsmith/otf-api/commit/cad2af241bd24d6aec572bf481b206fb0bfb5107)) - @NodeJSmith

- Merge pull request #7 from NodeJSmith/upgrade/switch_to_poetry

Upgrade/switch to poetry ([110d78a](https://github.com/nodejsmith/otf-api/commit/110d78a62d733320707103f8d65baafc4253e108)) - @NodeJSmith

- Remove generated docs
 ([340b501](https://github.com/nodejsmith/otf-api/commit/340b501856b75ecf04ebcce5169ec1f6260a0a99)) - @NodeJSmith

- Update gen logic
 ([01d9d78](https://github.com/nodejsmith/otf-api/commit/01d9d7851733e5bf6aa6b6696eb1dbe6c849e9b7)) - @NodeJSmith

- Update mkdocs config
 ([3de07ad](https://github.com/nodejsmith/otf-api/commit/3de07ad67477aa17b21a52dbbeb2c17399212dd5)) - @NodeJSmith

- Formatting, add black (mkdocs uses it)
 ([93bd88b](https://github.com/nodejsmith/otf-api/commit/93bd88b9cf51fc4cd50431d91e49dc98ec6965cb)) - @NodeJSmith

- Remove extra css
 ([d2e73f9](https://github.com/nodejsmith/otf-api/commit/d2e73f94b66135a47667f6ecb454cf547ebf2050)) - @NodeJSmith

- Update usage
 ([bc044fb](https://github.com/nodejsmith/otf-api/commit/bc044fbe695ffc4f1c41190810c509d8001eb88a)) - @NodeJSmith

- Add more stuff from the cookiecutter
 ([a1f4d15](https://github.com/nodejsmith/otf-api/commit/a1f4d151b0148afbbd82598cf71efb3e0e84c24a)) - @NodeJSmith

- Comment out/remove stuff that won't work/isn't needed
 ([60f21b3](https://github.com/nodejsmith/otf-api/commit/60f21b30c23916d6ba1ace3c7ebbe1699d80e1ab)) - @NodeJSmith

- Comment out code coverage action
 ([70f01e8](https://github.com/nodejsmith/otf-api/commit/70f01e8b93c7253564dc5a168fd51d997d1dd962)) - @NodeJSmith

- Switch setup-python to v5
 ([0aa81f2](https://github.com/nodejsmith/otf-api/commit/0aa81f292bba24e1718103d36ecda65bca62f6a5)) - @NodeJSmith

- Merge pull request #8 from NodeJSmith/feature/docs_cleanup

Clean up docs ([314c683](https://github.com/nodejsmith/otf-api/commit/314c683097210bfe4a99a21dedeb937f50a77fff)) - @NodeJSmith

- (docs): replace HISTORY.md with CHANGELOG.md for better change tracking
 ([b2fc07a](https://github.com/nodejsmith/otf-api/commit/b2fc07a5c08bef8dce025c0d388e20e0df1eea80)) - @NodeJSmith

- Add author and link
 ([5311d54](https://github.com/nodejsmith/otf-api/commit/5311d54f5e36653365a319aed295cbc102daddcf)) - @NodeJSmith


### Refactoring

- Change date_created and date_updated types from str to datetime for better date handling ([4c13b7b](https://github.com/nodejsmith/otf-api/commit/4c13b7b3bbab9862d9afbcaf426353f40f3e4a8d)) - @NodeJSmith

- Correct logger type hint to use string literal for forward reference ([9a200e8](https://github.com/nodejsmith/otf-api/commit/9a200e81f7f8ca34ceba1bd1513e977cbb77d452)) - @NodeJSmith

- Use centralized home_studio_uuid to simplify code ([ad98f82](https://github.com/nodejsmith/otf-api/commit/ad98f828c70364bbcd48c285481c706ae37c14f9)) - @NodeJSmith

- Streamline API class with direct member and studio details ([fb68b2c](https://github.com/nodejsmith/otf-api/commit/fb68b2c6950419c685940af5a3c958586f34cb21)) - @NodeJSmith

- Rename dna_api to telemetry_api ([f44f828](https://github.com/nodejsmith/otf-api/commit/f44f828d25cc582696fcd441666c9eba5584afa9)) - @NodeJSmith

- Rename studios_api ([cd03ba7](https://github.com/nodejsmith/otf-api/commit/cd03ba791ad62bedcd74c805fc9bc6386d4b4782)) - @NodeJSmith
