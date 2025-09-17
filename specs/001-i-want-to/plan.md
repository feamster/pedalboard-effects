# Implementation Plan: Guitar Pedalboard Effects Chain

**Branch**: `001-i-want-to` | **Date**: 2025-09-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-i-want-to/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Create a real-time guitar effects processing application using Spotify's pedalboard library for Python. The system processes audio input from a Scarlett interface through a configurable effects chain (boost → distortion → delay → reverb) with a UI for enabling/disabling effects and adjusting parameters. Audio routing supports BlackHole + Scarlett + external headphones.

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: pedalboard (Spotify), sounddevice, tkinter/PyQt, numpy
**Storage**: JSON files for presets
**Testing**: pytest with audio mocking
**Target Platform**: macOS (with Scarlett + BlackHole audio routing)
**Project Type**: single (desktop audio application)
**Performance Goals**: <10ms audio latency, real-time parameter updates
**Constraints**: Must work with existing audio setup (Scarlett input, BlackHole routing, external headphones)
**Scale/Scope**: Single-user desktop application, 4 core effects, extensible architecture

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (audio effects application)
- Using framework directly? (direct pedalboard usage, no wrappers)
- Single data model? (effects chain + parameters only)
- Avoiding patterns? (no unnecessary abstractions)

**Architecture**:
- EVERY feature as library? (audio_engine, effects_chain, ui_controller)
- Libraries listed:
  - audio_engine: handles I/O and real-time processing
  - effects_chain: manages effect ordering and parameters
  - ui_controller: provides interface for effect control
- CLI per library: audio-engine --help, effects-chain --help, ui-controller --help
- Library docs: llms.txt format planned

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (yes, tests written first)
- Git commits show tests before implementation? (will be enforced)
- Order: Contract→Integration→E2E→Unit strictly followed? (yes)
- Real dependencies used? (actual audio devices in tests where possible)
- Integration tests for: audio routing, effect parameter changes, preset loading
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? (yes, for audio processing and errors)
- Frontend logs → backend? (desktop app, single process logging)
- Error context sufficient? (audio device errors, effect processing failures)

**Versioning**:
- Version number assigned? (1.0.0)
- BUILD increments on every change? (yes)
- Breaking changes handled? (effect parameter compatibility)

## Project Structure

### Documentation (this feature)
```
specs/001-i-want-to/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Option 1 (single desktop application project)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Audio latency requirements and achievable latency with pedalboard
   - Best practices for real-time audio processing in Python
   - Optimal audio buffer sizes for Scarlett interfaces
   - Integration patterns for BlackHole audio routing

2. **Generate and dispatch research agents**:
   ```
   Task: "Research pedalboard library real-time capabilities and latency optimization"
   Task: "Find best practices for Python real-time audio with sounddevice"
   Task: "Research Scarlett audio interface configuration for low latency"
   Task: "Investigate BlackHole audio routing setup and integration"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - EffectsChain: ordered list of effects with parameters
   - AudioEffect: individual effect with type, parameters, bypass state
   - Preset: saved configuration with metadata
   - AudioInterface: connection to hardware with routing info

2. **Generate API contracts** from functional requirements:
   - Audio processing interface (start/stop/process)
   - Effect management interface (add/remove/reorder)
   - Parameter control interface (get/set/reset)
   - Preset management interface (save/load/delete)
   - Output contracts to `/contracts/`

3. **Generate contract tests** from contracts:
   - Test files for each interface
   - Assert audio processing contracts
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Real-time audio processing scenario
   - Effect parameter adjustment scenario
   - Effect chain reordering scenario
   - Preset save/load scenario

5. **Update CLAUDE.md incrementally**:
   - Add pedalboard and audio processing context
   - Include project-specific audio routing setup
   - Preserve manual additions between markers
   - Keep under 150 lines for token efficiency

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before UI
- Audio-specific: Core audio engine before effects before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations identified for this implementation.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*