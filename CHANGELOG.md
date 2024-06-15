# Changelog

All notable changes to this project will be documented in this file. See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

## [unreleased]

### Bug Fixes

- Change cr_waitlist_flag_last_updated type from str to datetime for accuracy ([4310693](4310693e4f8c135bb7a60e1d196e6cf84f1f788f))

- Change type of cr_waitlist_flag_last_updated from str to datetime for accuracy ([086370f](086370fae472f12fe420e6500edbbbb3773ab11e))

- Change type of cr_waitlist_flag_last_updated from str to datetime for accurate representation of date/time values ([18e80d0](18e80d0a405ba7c11326b8b174ae540e8a63eec9))

- Fix pyproject, get tox working, add first test
 ([287a53e](287a53e5957b8a6377c0f23cacba94332f75be10))

- Fix mypy errors
 ([e654e2e](e654e2e6ee985cc254e9a86ec3e9d44d2a25d8cb))

- Fix tox
 ([a37e4c6](a37e4c6fdc025ef8a4fcadf57890f0307ae709fe))

- Fix docstrings for griffe
 ([764e61c](764e61c4a4624aebfc06e1cf8cd39f28d4639b66))

- Fix extra - should be docs, not doc
 ([992b6ff](992b6ff7b78a7de16f05a0372fa5d55d395c476f))

- Fix(tox.ini): replace poetry with pipx in deps to manage dependencies
feat(tox.ini): add pipx install poetry in commands_pre to ensure poetry is installed
 ([eefb5b3](eefb5b3320f658550b0c7a353fda2ecdc8dbb059))

- Add poetry install command to ensure dev dependencies are installed before running checks ([3f6957f](3f6957f7cb2cdaa5dbea703d84d39cc64f786b30))

- Fix reference to dna
 ([2b6443c](2b6443c7dfdee96b7bcbc889c13b6f207a98e647))


### Documentation

- Docs
 ([5c23abf](5c23abfd05671ba3780eb8f6312260a0cb37b55f))

- Docstrings, make some members private
 ([0263298](02632986a3c74dcffe5c2b33e32ca2f46d065eed))


### Features

- Add literal_eval import and use for parsing HR data ([c2b2899](c2b28990a55ef5c3d6c574d2eb176154a445c06b))

- Enhance header handling in API requests to allow custom headers ([11e42eb](11e42ebec0a076014e8eddebd80f67c773cf3597))

- Feat(api.py): enforce username and password as required for Api class
feat(api.py): add class method to create Api instance with user details
docs(api.py): update constructor docstring to explain username and password necessity
feat(api.py): introduce member home studio and timezone attributes in Api class
 ([def9aca](def9aca25bc3001ab897f63b9f74df410839b610))

- Integrate PerformanceApi for performance data handling ([020d6d5](020d6d5a9e2d961fc57e6427101aacaf8f835dad))

- Introduce OtfBaseModel with model_config for shared configuration ([70781b6](70781b6f0e63cce1ebaa69024d97adc5d947572f))


### Miscellaneous Chores

- Pin dependencies to specific versions for consistent builds ([656e3ab](656e3ab4bf7464a54d317347bd2262bca23e5689))

- Chore(pyproject.toml): add pre-commit and mypy to dev dependencies for code quality
chore(pyproject.toml): pin versions for mkdocs and related plugins to ensure compatibility
 ([a4fadbf](a4fadbf9364b016d0e98660f13eb809eccdf3861))

- Chore(tox.ini): remove skipsdist option to enable source distribution
chore(tox.ini): add allowlist_externals for lint and build environments
chore(tox.ini): update allowlist_externals in default testenv
chore(tox.ini): add commands_pre to ensure dependencies are installed
chore(tox.ini): update pytest command to use importlib import mode
 ([c09ee88](c09ee8825ecaaf1ea28ed7b2737c724e8d93fdc8))

- Add commands_pre section with echo to ensure pre-commands run before main commands ([a6acddd](a6acddd54a44144512d52fb1fcf39404b8ba7df7))

- Chore(tox.ini): replace echo with comment symbol in commands_pre to clean up configuration
chore(tox.ini): update allowlist_externals to include only necessary tools poetry and pipx
 ([b76a5ce](b76a5ce650825bd7f028b0437aa3d15e33fe0f99))

- Chore(pre-commit): add mypy and commitizen hooks to pre-commit config
refactor(telemetry): replace TelemetryItem with Telemetry in telemetry API
fix(models): update imports and __all__ to reflect Telemetry changes
feat(models): add Telemetry model to handle telemetry data
 ([63feb5f](63feb5f9109a5af06f5716a2aab011e0fa3b755c))

- Remove commitizen hook configuration to streamline pre-commit checks ([c439a79](c439a791d1de42bdb59847895240fb9f8ffe4ac8))


### Other (unconventional)

- Initial commit
 ([1a86683](1a86683da24e1b462183310f28476dbe3c5a211f))

- Add scratch to gitignore
 ([41ff851](41ff8514f7379e9094ac01d8f20c27e5c4a5346d))

- Add _get_bookings_old for documentation, add more notes to get_bookings
 ([87ee9db](87ee9db5ee0087f3ec539ef27fd0a63fbe8209a4))

- Make class optional
 ([ec46e3c](ec46e3ca981ec308cf0f04bf55b81d0a597b6e5a))

- Add all_statuses to HistoryBookingStatus
 ([5111ddb](5111ddbbe5bc06d5ec750b707af36139986f3e83))

- Add new files, update pyproject
 ([70e9df5](70e9df5a0295ef562d12204dfbdf0da80739c02b))

- Add tox.ini and github workflow
 ([c11da57](c11da575e26472a4c8922fb6e0b5f9045cfd6e73))

- Update action
 ([d441aaf](d441aaf8d6fd7e3bb72b5bce3890405ccc6518b2))

- Add cache pip
 ([6122ca6](6122ca6f1836cedd689b6cf7cc2f8a8a8d27fc1a))

- Add python version to cache keys
 ([d074c68](d074c68f2e67e772c4dc974826a3518e5c0c61fe))

- Update to node 20
 ([78535fe](78535fe3af3681d4b3cfe6b94b8e9a0ffc51c8cd))

- Merge pull request #1 from NodeJSmith/feature/add_perf_summary_api

Feature/add perf summary api - lots of improvements, not just performance summary. not bothering with bump since not published yet ([34836ff](34836fffef2059e56dc84f5d2ddc5508ad98a51b))

- Start adding md files, docs, tests, etc
 ([3caca8b](3caca8b687f6012ec2ac6259ae051b5faee946bc))

- More docs stuff
 ([4666c71](4666c719ac886d67044e56ec8bcd8114ee654d7e))

- Merge pull request #2 from NodeJSmith/feature/make_user_friendly

feature/make user friendly ([3ae7dcf](3ae7dcfb267582332698e61ce9d406d701222178))

- Renaming everything to oft-api
 ([8906eaa](8906eaa9db791b46d7f7e170aac686d04013131a))

- Add examples and add more to usage page
 ([6b38dad](6b38dad346db995d02eb3ef7d72dc2d8b0fda4e9))

- Correct location
 ([6ab8a0e](6ab8a0e472c27c44ff222e476ad9c1ece2fbe052))

- Create dependabot.yml ([acb8574](acb8574d668a8b08e17e8ea783a4eb862419296f))

- Update action to run test and lint separate
 ([61ef2df](61ef2df24f8771eb7d0610d49124863889b7f436))

- Add verbose flags to tox
 ([c9ce530](c9ce53053133b16d27b86005771604237c4501f6))

- Add mkdocs build step directly
 ([3701fe5](3701fe55fa92993611997d22089e1958a9e1c017))

- Install dev and docs deps first, comment out other steps for now
 ([c1ddf17](c1ddf1786393f2ec600aee3150283c50a45d3186))

- Tweak tox.ini
 ([a08de7a](a08de7a1548c2916b46ba3d571764a2cc9e3899c))

- Add env
 ([a302519](a302519a8b9b08b50ec5c0225d18a2ec85cc7c36))

- Use matrix version when running tox
 ([e77dd54](e77dd54ef80d9a62527f307061f52fc80df3a12c))

- Merge pull request #6 from NodeJSmith/fix/tox

Fix tox lint stage ([9e64811](9e648114482b593471d8313b68d44b6d6ff44461))

- Switch to poetry to simplify tox
 ([732192d](732192d700d31ab09720815e40a8f70410af54bd))

- Add build checks to GitHub Actions workflow to ensure package builds correctly ([c5a2afe](c5a2afe7f2686416144e2e2424cec8e4f7e4f3b4))

- Increase verbosity of tox commands to improve debugging and output clarity ([cf44695](cf4469535d760335cdd8d8d20bcab6c6cfa4070e))

- Remove verbose flag from tox commands to reduce log output ([bbf91e6](bbf91e656abeca9daf09fbb8d30a607717004694))

- Add mkdocs build step to GitHub Actions workflow ([cad2af2](cad2af241bd24d6aec572bf481b206fb0bfb5107))

- Merge pull request #7 from NodeJSmith/upgrade/switch_to_poetry

Upgrade/switch to poetry ([110d78a](110d78a62d733320707103f8d65baafc4253e108))

- Remove generated docs
 ([340b501](340b501856b75ecf04ebcce5169ec1f6260a0a99))

- Update gen logic
 ([01d9d78](01d9d7851733e5bf6aa6b6696eb1dbe6c849e9b7))

- Update mkdocs config
 ([3de07ad](3de07ad67477aa17b21a52dbbeb2c17399212dd5))

- Formatting, add black (mkdocs uses it)
 ([93bd88b](93bd88b9cf51fc4cd50431d91e49dc98ec6965cb))

- Remove extra css
 ([d2e73f9](d2e73f94b66135a47667f6ecb454cf547ebf2050))

- Update usage
 ([bc044fb](bc044fbe695ffc4f1c41190810c509d8001eb88a))

- Add more stuff from the cookiecutter
 ([a1f4d15](a1f4d151b0148afbbd82598cf71efb3e0e84c24a))

- Comment out/remove stuff that won't work/isn't needed
 ([60f21b3](60f21b30c23916d6ba1ace3c7ebbe1699d80e1ab))

- Comment out code coverage action
 ([70f01e8](70f01e8b93c7253564dc5a168fd51d997d1dd962))

- Switch setup-python to v5
 ([0aa81f2](0aa81f292bba24e1718103d36ecda65bca62f6a5))

- Merge pull request #8 from NodeJSmith/feature/docs_cleanup

Clean up docs ([314c683](314c683097210bfe4a99a21dedeb937f50a77fff))

- (docs): replace HISTORY.md with CHANGELOG.md for better change tracking
 ([b2fc07a](b2fc07a5c08bef8dce025c0d388e20e0df1eea80))


### Refactoring

- Change date_created and date_updated types from str to datetime for better date handling ([4c13b7b](4c13b7b3bbab9862d9afbcaf426353f40f3e4a8d))

- Correct logger type hint to use string literal for forward reference ([9a200e8](9a200e81f7f8ca34ceba1bd1513e977cbb77d452))

- Use centralized home_studio_uuid to simplify code ([ad98f82](ad98f828c70364bbcd48c285481c706ae37c14f9))

- Streamline API class with direct member and studio details ([fb68b2c](fb68b2c6950419c685940af5a3c958586f34cb21))

- Rename dna_api to telemetry_api ([f44f828](f44f828d25cc582696fcd441666c9eba5584afa9))

- Rename studios_api ([cd03ba7](cd03ba791ad62bedcd74c805fc9bc6386d4b4782))
