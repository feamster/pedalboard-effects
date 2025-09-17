# Tasks: Guitar Pedalboard Effects Chain

**Input**: Design documents from `/specs/001-i-want-to/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Create project structure with src/ and tests/ directories
- [ ] T002 Initialize Python project with requirements.txt for pedalboard>=0.7.0, PyQt6, numpy, sounddevice
- [ ] T003 [P] Configure pytest.ini and setup basic Python project structure

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Core Model Tests
- [ ] T004 [P] Test EffectsChain model creation and validation in tests/unit/test_effects_chain.py
- [ ] T005 [P] Test AudioEffect model with BOOST/DISTORTION/DELAY/REVERB types in tests/unit/test_audio_effect.py
- [ ] T006 [P] Test Preset model save/load functionality in tests/unit/test_preset.py

### Audio Processing Tests
- [ ] T007 [P] Test audio processing interface contract in tests/contract/test_audio_processing.py
- [ ] T008 [P] Test effects management interface contract in tests/contract/test_effects_management.py
- [ ] T009 [P] Test preset management interface contract in tests/contract/test_preset_management.py

### Integration Tests
- [ ] T010 [P] Test real-time audio processing scenario in tests/integration/test_audio_flow.py
- [ ] T011 [P] Test effect parameter adjustment scenario in tests/integration/test_parameter_control.py
- [ ] T012 [P] Test preset save/load scenario in tests/integration/test_preset_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models
- [ ] T013 [P] EffectsChain model class in src/models/effects_chain.py
- [ ] T014 [P] AudioEffect model class with parameter validation in src/models/audio_effect.py
- [ ] T015 [P] Preset model class with JSON serialization in src/models/preset.py
- [ ] T016 [P] AudioInterface model for device configuration in src/models/audio_interface.py

### Core Services
- [ ] T017 AudioEngine service using pedalboard AudioStream in src/services/audio_engine.py
- [ ] T018 EffectsManager service for chain management in src/services/effects_manager.py
- [ ] T019 PresetManager service for configuration persistence in src/services/preset_manager.py
- [ ] T020 ConfigurationService for app settings and device config in src/services/config_service.py

### User Interface
- [ ] T021 Main application window with PyQt6 in src/ui/main_window.py
- [ ] T022 [P] Effects control panel with sliders and toggles in src/ui/effects_panel.py
- [ ] T023 [P] Audio settings dialog for device selection in src/ui/audio_settings.py
- [ ] T024 [P] Preset browser and manager UI in src/ui/preset_browser.py

### Application Entry Point
- [ ] T025 Main entry script with argument parsing in src/main.py
- [ ] T026 CLI module for command-line operations in src/cli/pedalboard_cli.py

## Phase 3.4: Integration
- [ ] T027 Connect AudioEngine to EffectsManager for real-time processing
- [ ] T028 Integrate UI controls with effects parameter updates
- [ ] T029 Wire preset save/load functionality to UI
- [ ] T030 Add error handling and user feedback for audio device issues
- [ ] T031 Implement configuration persistence for audio settings

## Phase 3.5: Polish
- [ ] T032 [P] Unit tests for parameter validation in tests/unit/test_parameter_validation.py
- [ ] T033 [P] Unit tests for audio device management in tests/unit/test_device_management.py
- [ ] T034 Performance test for audio latency measurement in tests/performance/test_latency.py
- [ ] T035 [P] Update quickstart.md with actual usage examples
- [ ] T036 Add logging and debugging capabilities
- [ ] T037 Run complete integration test suite from quickstart.md

## Dependencies
- Setup (T001-T003) before all other tasks
- Tests (T004-T012) before implementation (T013-T026)
- Models (T013-T016) before services (T017-T020)
- Services before UI (T021-T024)
- Core implementation before integration (T027-T031)
- Integration before polish (T032-T037)

## Parallel Example - Initial Test Setup
```bash
# Launch T004-T006 together (model tests):
Task: "Test EffectsChain model creation and validation in tests/unit/test_effects_chain.py"
Task: "Test AudioEffect model with effect types in tests/unit/test_audio_effect.py"
Task: "Test Preset model save/load functionality in tests/unit/test_preset.py"

# Launch T007-T009 together (contract tests):
Task: "Test audio processing interface contract in tests/contract/test_audio_processing.py"
Task: "Test effects management interface contract in tests/contract/test_effects_management.py"
Task: "Test preset management interface contract in tests/contract/test_preset_management.py"
```

## Parallel Example - Model Implementation
```bash
# Launch T013-T016 together (data models):
Task: "EffectsChain model class in src/models/effects_chain.py"
Task: "AudioEffect model class with parameter validation in src/models/audio_effect.py"
Task: "Preset model class with JSON serialization in src/models/preset.py"
Task: "AudioInterface model for device configuration in src/models/audio_interface.py"
```

## Parallel Example - UI Components
```bash
# Launch T022-T024 together (UI components):
Task: "Effects control panel with sliders and toggles in src/ui/effects_panel.py"
Task: "Audio settings dialog for device selection in src/ui/audio_settings.py"
Task: "Preset browser and manager UI in src/ui/preset_browser.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Focus on simple start script with UI and configuration saving as requested
- Use PyQt6 as the chosen UI framework based on research findings
- Pedalboard library provides the core audio processing capabilities

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each interface → service implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks

3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → UI → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task

## Simplified Focus
Based on user requirements: "start a script, get a UI, save configurations"
- T025: Main entry script (python src/main.py)
- T021: PyQt6 UI with effects controls
- T019: Preset saving/loading functionality
- Core audio processing with pedalboard integration