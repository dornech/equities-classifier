# Changelog

## Version 0.0.1 (development)

- First pre-alpha
- ...

## [v0.8.0](https://github.com/dornech/equities-classifier/releases/tag/v0.8.0)  (2026-08-20) 

### Features

- Country-postfix for tickers and fix comprehension in OpenFIGI and Morningstar incl. test cases
(['f22b785'](https://github.com/dornech/equities-classifier/commit/f22b78550d4c5f483dc6a7cbf6b4251b0031dd35))
- In-/output incl. test cases
(['88cf17b'](https://github.com/dornech/equities-classifier/commit/88cf17bcbc7aa90785f507156435a3b540db7a0a))

### Bug fixes

- Improve Morningstar selection regarding ticker processing
(['8393476'](https://github.com/dornech/equities-classifier/commit/8393476f3220f7d919f1505a78cae7e5c875aea9))
- Improve OpenFIGI record comprehension
(['112f5d2'](https://github.com/dornech/equities-classifier/commit/112f5d242f8650d4722cf56533bce37d1f843f2f))

## [v0.7.2](https://github.com/dornech/equities-classifier/releases/tag/v0.7.2)  (2026-08-18) 

### Bug fixes

- Further finetuning for Chrome test on GitHub
(['74c62e8'](https://github.com/dornech/equities-classifier/commit/74c62e82bb7517933834f6db2c34af84159cc203))
- Template improvements regarding optional browser tests, fixes
(['3d96bb0'](https://github.com/dornech/equities-classifier/commit/3d96bb0ca7e7c3fc60d981af9ac75c343fde04b8))
- Allow browser tests on GitHub Action by adding Chrome installer action, correct browser fixtures
(['b138254'](https://github.com/dornech/equities-classifier/commit/b1382548392c6a8e748e69a641fc1053fd1edb58))
- No testcases marked local considered in GitHub Action for build-test
(['5da374e'](https://github.com/dornech/equities-classifier/commit/5da374e5f30cef908fb41102d179c196903fcfbf))

### Testing


## [v0.7.1](https://github.com/dornech/equities-classifier/releases/tag/v0.7.1)  (2026-08-16) 

### Features

- Logging and some refinement on client error handling
(['5d704fb'](https://github.com/dornech/equities-classifier/commit/5d704fbb9173419cfcd0227ea4de655e8ef9aabe))
- Include py-gcis to enrich/validate GICS information from Motely Fool
(['053644e'](https://github.com/dornech/equities-classifier/commit/053644ebd911d10b6ee4a827588feef45fca95b0))

### Bug fixes

- Processflow - openfigi always first to ensure ISIN and ticker
(['0817aea'](https://github.com/dornech/equities-classifier/commit/0817aea2ca2e658fd3d5b75c58f5fc7b4eacfc03))
- Improve conftest.py
(['e026111'](https://github.com/dornech/equities-classifier/commit/e02611124cfdbaf7776bb82003ae84f0d40dab5d))

## [v0.7.0](https://github.com/dornech/equities-classifier/releases/tag/v0.7.0)  (2026-08-15) 

### Features

- Template improvements - reorganize/group tests, dependency check in pre-commit
(['5177f72'](https://github.com/dornech/equities-classifier/commit/5177f72c568867142d6309fc77972ee8ef3e7c71))
- Classification logic and integration into process flow core logic
(['5ccefb0'](https://github.com/dornech/equities-classifier/commit/5ccefb0f2204e6543cab6eb10e094f83334ca79b))
- Process flow core logic
(['150987c'](https://github.com/dornech/equities-classifier/commit/150987c932b3c2d9ce8dd3dc1e4382c21f215934))

### Bug fixes

- Docsig error in GitHub Action
(['4cb4222'](https://github.com/dornech/equities-classifier/commit/4cb422245bc23045a237008f948ad551b4677181))
- Partial redesign MotleyFoolClient to add Selenium mode, reorganize tests
(['5f1c42b'](https://github.com/dornech/equities-classifier/commit/5f1c42b3a7a9cc46a11e8d3c2d1a2fad82e5781c))
- Treat RUF, mypy and docsig errors occurring on GitHub
(['5a84a9d'](https://github.com/dornech/equities-classifier/commit/5a84a9d29bf8258722bcb9d72510db7fe9245f49))
- Treat RUF and mypy errors
(['1626007'](https://github.com/dornech/equities-classifier/commit/1626007cd78d726feb8a55ade4380eebd220a894))

### Build system

- **deps**: Bump release-drafter/release-drafter from 7 to 7.6.0
 (['af881c3'](https://github.com/dornech/equities-classifier/commit/af881c324f5ef08a7945af8dbf2bd44d167ece76))
- **deps**: Bump sigstore/gh-action-sigstore-python from 3.4.0 to 3.5.0
 (['b1a7108'](https://github.com/dornech/equities-classifier/commit/b1a71083cab762c755eb799e608f415320617dfc))

## [v0.6.0](https://github.com/dornech/equities-classifier/releases/tag/v0.6.0)  (2026-08-12) 

### Features

- Matching and merging for SecurityProviderRecords incl. test cases
(['fde59a1'](https://github.com/dornech/equities-classifier/commit/fde59a130900c04566a22a1ddaa5f1d66b46db2b))
- Template improvements - reorganize/group tests, dependency check in pre-commit
(['199fbbe'](https://github.com/dornech/equities-classifier/commit/199fbbee44acdf968e0f0470aff3fc10346d4a16))

### Bug fixes

- Switch from undetected-chromedriver to undetected, add missing dependency lxml
(['6eb361d'](https://github.com/dornech/equities-classifier/commit/6eb361d8ab08e930e6d2936ad318f82634796dbd))

## [v0.5.1](https://github.com/dornech/equities-classifier/releases/tag/v0.5.1)  (2026-08-09) 

### Features

- MotleyFool client with dynamic determination "Next-Action" code, alignment error handling of of clients
(['ec708c8'](https://github.com/dornech/equities-classifier/commit/ec708c8f504aa487b57d9d200ea066d7182ffcac))

### Bug fixes

- Updated pyproject.toml regarding dependencies
(['a15743f'](https://github.com/dornech/equities-classifier/commit/a15743f704e52d1f27bf45946d6529d70e0ec099))
- Missing docstrings
(['4e51f30'](https://github.com/dornech/equities-classifier/commit/4e51f30311e74c3697f3964b4d27e187b01dabf5))
- Small corrections for alignment error handling, mypy-fixes, other smaller fixes and clean-ups
(['96a1cfe'](https://github.com/dornech/equities-classifier/commit/96a1cfe02d0879be96b1543c76a5192d9616b6db))
- Optimize GitHub actions resource usage, avoid especially very expensive macOS-actions
(['0910fee'](https://github.com/dornech/equities-classifier/commit/0910fee0ed47b5cc6c377ee250ae79b8a7ba0204))

## [v0.5.0](https://github.com/dornech/equities-classifier/releases/tag/v0.5.0)  (2026-08-06) 

### Features

- MotleyFool client (for classification) including test cases
(['06fa443'](https://github.com/dornech/equities-classifier/commit/06fa443fdb9d41365abbf348fdb401f5b6c7dd55))

### Bug fixes

- Improvement OpenFIGI ans Morningstar clients and test further ruff fixes
(['e371d7f'](https://github.com/dornech/equities-classifier/commit/e371d7fe3a872bfe35a78d5ac2e3f0465b8476ef))
- Various fixes to overcome GitHub lint issues and clean ups
(['8df8fea'](https://github.com/dornech/equities-classifier/commit/8df8fead70db1b42ce9b63363748e43bb9d58314))

## [v0.4.1](https://github.com/dornech/equities-classifier/releases/tag/v0.4.1)  (2026-08-05) 

### Bug fixes

- Cleanup and regression test openfigi
(['c6abfdd'](https://github.com/dornech/equities-classifier/commit/c6abfdd8f49d395956ed436c7427a21858e1a236))
- Tests and fixes for Morningstar client
(['d00ade4'](https://github.com/dornech/equities-classifier/commit/d00ade4421b8740e9fb5a8835fd939e324a5b646))
- Ruff errors in Morningstar client
(['34f9e37'](https://github.com/dornech/equities-classifier/commit/34f9e37d38008add042c40378c1b3c9d4ab43e0b))

## [v0.4.0](https://github.com/dornech/equities-classifier/releases/tag/v0.4.0)  (2026-08-05) 

### Features

- Morningstar connector 3rd try with Selenium / undetected-chromedriver
(['3f4ebe1'](https://github.com/dornech/equities-classifier/commit/3f4ebe17e4b7a79e1978916cf05c97a64f6d9556))
- Morningstar connector 2nd try with anti-bot detection
(['46f925e'](https://github.com/dornech/equities-classifier/commit/46f925edadff70e4684261dedccb1b999b5ee894))
- Morningstar connector 2nd try
(['8f5f34f'](https://github.com/dornech/equities-classifier/commit/8f5f34ff3df2439834173ebfead3ab8447ae49e9))
- Morningstar connector 1st try
(['c09173e'](https://github.com/dornech/equities-classifier/commit/c09173e3aff61ad1d8ca8623e7030d44ca9c9fbf))

### Bug fixes

- Morningstar connector (better call it client) improvements and testcases
(['a78f02f'](https://github.com/dornech/equities-classifier/commit/a78f02fa1c9a64343488c2bb237337aff839088d))

### Chores

- Clean up data model, delete resolver/connector
(['2539243'](https://github.com/dornech/equities-classifier/commit/25392438214484c44df077f1e4bda87d4fe0a906))
- Archive latest changes resolver/connector before deleting
(['74015ff'](https://github.com/dornech/equities-classifier/commit/74015ff6d44d5d80fd67b5b2d1b93a99d071da89))

## [v0.3.2](https://github.com/dornech/equities-classifier/releases/tag/v0.3.2)  (2026-08-01) 

### Bug fixes

- OpenFIGI client - testcase with http-request and corrections
(['d6bab53'](https://github.com/dornech/equities-classifier/commit/d6bab532eeb5061627721b6592bf0dbb6b12a267))

## [v0.3.1](https://github.com/dornech/equities-classifier/releases/tag/v0.3.1)  (2026-08-01) 

### Bug fixes

- OpenFIGI client - testcases and corrections
(['2996b57'](https://github.com/dornech/equities-classifier/commit/2996b57479fa210cb51b31e3c9207aab6252d1b3))
- OpenFIGI client - use SHARE_CLASS_FIGI instead FIGI
(['57ea785'](https://github.com/dornech/equities-classifier/commit/57ea785b2f43414d26463fd45a7857c2b016219f))

## [v0.3.0](https://github.com/dornech/equities-classifier/releases/tag/v0.3.0)  (2026-08-01) 

### Features

- OpenFIGI client
(['f2fb32f'](https://github.com/dornech/equities-classifier/commit/f2fb32fe8198c236db12003ddd4d1a8c796c0a28))

## [v0.2.0](https://github.com/dornech/equities-classifier/releases/tag/v0.2.0)  (2026-07-30) 

### Features

- Add abstract resolver and connector interfaces
(['e93b9c3'](https://github.com/dornech/equities-classifier/commit/e93b9c36fb6e44417fb7aae6d29b3e2c0e55034a))

## [v0.1.0](https://github.com/dornech/equities-classifier/releases/tag/v0.1.0)  (2026-07-30) 

### Features

- Initial domain model
(['60fd9a1'](https://github.com/dornech/equities-classifier/commit/60fd9a149a133f5a0114a9e7168b51d4b3d672d7))
- Set up project based on ChatGPT input
(['f80409e'](https://github.com/dornech/equities-classifier/commit/f80409e3aa57f71ff71902dea4ca364607098102))

### Bug fixes

- Adjust pyproject.toml
(['ee723ab'](https://github.com/dornech/equities-classifier/commit/ee723ab428cf5f524a1acee2fd9496ab8846204a))
