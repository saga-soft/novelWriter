"""
novelWriter - Project Data Tests
================================

This file is a part of novelWriter
Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""  # noqa

from __future__ import annotations

from datetime import date

import pytest

from novelwriter import CONFIG
from novelwriter.core import projectdata
from novelwriter.core.project import NWProject
from novelwriter.core.projectdata import ProjectData
from novelwriter.enum import nwItemClass

from tests.helpers import C, buildTestProject


class MockProject:
    """Fake project object that just counts change notifications."""

    def __init__(self) -> None:
        self.changed = 0

    def setProjectChanged(self, state: bool) -> None:
        """Fake project method."""
        self.changed += 1 if state else 0

    def markCountsDirty(self) -> None:
        """Fake project method."""


class _FakeDate(date):
    """A date subclass where 'today' can be pinned by a test so that
    the clock transition to a new day can be simulated.
    """

    _today = date(2026, 7, 20)

    @classmethod
    def today(cls) -> date:
        """Return the pinned 'today' value."""
        return cls._today


@pytest.mark.core
def testProjectData_Uuid(mockGUI):
    """Test the setUuid setter."""
    project = MockProject()
    data = ProjectData(project)  # type: ignore

    # An empty/invalid value generates a new uuid
    data.setUuid("not-a-uuid")
    assert data.uuid != ""
    firstUuid = data.uuid

    # Setting the same uuid again does nothing
    project.changed = 0
    data.setUuid(firstUuid)
    assert data.uuid == firstUuid
    assert project.changed == 0

    # Setting a new, valid uuid updates it and flags the change
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert data.uuid == "d0f3fe10-c6e6-4310-8bfd-181eb4224eed"
    assert project.changed == 1


@pytest.mark.core
def testProjectData_Language(mockGUI):
    """Test the setLanguage setter."""
    project = MockProject()
    data = ProjectData(project)  # type: ignore

    data.setLanguage("en_GB")
    assert data.language == "en_GB"

    # Setting the same language again does nothing
    project.changed = 0
    data.setLanguage("en_GB")
    assert data.language == "en_GB"
    assert project.changed == 0


@pytest.mark.core
def testProjectData_LastHandle(mockGUI):
    """Test the setLastHandle and setInitLastHandles setters."""
    project = MockProject()
    data = ProjectData(project)  # type: ignore

    # Setting with a non-string component does nothing
    project.changed = 0
    data.setLastHandle("0123456789abc", None)  # type: ignore
    assert project.changed == 0

    # Setting with a valid component works
    data.setLastHandle("0123456789abc", "editor")
    assert data.getLastHandle("editor") == "0123456789abc"

    # setInitLastHandles requires a dict
    project.changed = 0
    data.setInitLastHandles(["not", "a", "dict"])  # type: ignore
    assert project.changed == 0

    # Unknown keys in the dict are skipped, known keys are updated
    data.setInitLastHandles({"unknownKey": "0123456789abc", "editor": "0123456789abd"})
    assert data.getLastHandle("editor") == "0123456789abd"


@pytest.mark.core
def testProjectData_CurrCounts(mockGUI):
    """Test the setCurrCounts setter."""
    project = MockProject()
    data = ProjectData(project)  # type: ignore

    data.setCurrCounts(1, 2, 3, 4)
    assert data.currCounts == (1, 2, 3, 4)

    # Only the given values are updated, others are left as-is
    data.setCurrCounts(wNovel=None, wNotes=None, cNovel=9, cNotes=None)
    assert data.currCounts == (1, 2, 9, 4)


@pytest.mark.core
def testProjectData_AutoReplace(mockGUI):
    """Test the setAutoReplace setter."""
    project = MockProject()
    data = ProjectData(project)  # type: ignore

    # Requires a dict
    project.changed = 0
    data.setAutoReplace(["not", "a", "dict"])  # type: ignore
    assert project.changed == 0
    assert data.autoReplace == {}

    # Non-string entries are skipped
    data.setAutoReplace({"A": "B", "C": 123})  # type: ignore
    assert data.autoReplace == {"A": "B"}

    # Keys are cleaned too, not just values, as both end up in the
    # project XML, and a key that is only control characters is dropped
    data.setAutoReplace({"foo\x1b": "bar\x1b", "\x00\x07": "baz"})
    assert data.autoReplace == {"foo": "bar"}


@pytest.mark.core
def testProjectData_ProjectTarget(mockGUI):
    """Test the setProjectTarget setter, including the count mode flag
    that decides whether the project goal is tracked in words or
    characters.
    """
    project = MockProject()

    # The count mode defaults to the user's global preference
    CONFIG.useCharCount = True
    assert ProjectData(project).targetCountChars is True  # type: ignore
    CONFIG.useCharCount = False
    data = ProjectData(project)  # type: ignore
    assert data.targetCountChars is False

    # Setting the target updates the count, deadline and count mode together
    project.changed = 0
    data.setProjectTarget(50000, date(2030, 1, 1), True)
    assert data.targetCount == 50000
    assert data.targetDeadline == date(2030, 1, 1)
    assert data.targetCountChars is True
    assert project.changed == 1

    # Setting the exact same values again is a no-op
    project.changed = 0
    data.setProjectTarget(50000, date(2030, 1, 1), True)
    assert project.changed == 0

    # Toggling the count mode alone still counts as a change
    project.changed = 0
    data.setProjectTarget(50000, date(2030, 1, 1), False)
    assert data.targetCountChars is False
    assert project.changed == 1


@pytest.mark.core
def testProjectData_TargetSkipRoots(mockGUI, mockRnd, fncPath, ipsumText):
    """Test the setTargetSkipRoots setter against a real project tree.
    The daily progress is tracked per item from the session baseline,
    so excluding or including a root only changes today's progress by
    what was actually written in that root this session, not by its
    full word count, and re-setting the same roots must be a no-op.
    """
    project = NWProject()
    buildTestProject(project, fncPath)
    tree = project.tree

    # Add a second Novel root folder with a file of lorem ipsum text,
    # written before the session baseline below is established
    secondRoot = project.newRoot(nwItemClass.NOVEL)
    secondDoc = project.newFile("Second Chapter", secondRoot) or ""
    project.storage.getDocument(secondDoc).writeDocument("## Second Chapter\n\n" + ipsumText[0])
    project.index.reIndexHandle(secondDoc)

    secondWords = tree[secondDoc].wordCount  # type: ignore
    assert secondWords > 0

    # Reload the project so the per-item session baseline is set to the
    # word counts as they stand now, as if the project had just been
    # opened with both Novel roots counted. The daily progress carried
    # over from the earlier in-memory build isn't relevant here, so it
    # is explicitly reset to a known-zero starting point
    project.saveProject(autoSave=True)
    assert project.openProject(fncPath) is True
    data = project.data
    tree = project.tree
    data.setProjectTarget(10000, None, False)
    data.resetDailyProgress()

    startWords = tree.sumCounts()[5]
    assert data.targetSkipRoots == set()
    assert data.dailyProgress == 0
    assert data.targetLastCount == startWords

    # Some more text is written in the original chapter, in a root that
    # stays included, which shows up as today's progress
    doc = project.storage.getDocument(C.hSceneDoc)
    doc.writeDocument((doc.readDocument() or "") + "\n\n" + ipsumText[1])
    project.index.reIndexHandle(C.hSceneDoc)
    project.updateCounts()

    writtenWords = data.dailyProgress
    newWords = tree.sumCounts()[5]
    assert writtenWords > 0
    assert data.targetLastCount == newWords

    # Excluding the second root drops the project total by its word
    # count, but since none of those words were written this session,
    # today's progress is unaffected
    project.setProjectChanged(False)
    data.setTargetSkipRoots([secondRoot])
    assert project.projChanged is True
    assert data.targetSkipRoots == {secondRoot}
    assert data.targetLastCount == newWords - secondWords
    assert data.dailyProgress == writtenWords

    # Setting the same root again, even wrapped in a fresh list, is a no-op
    project.setProjectChanged(False)
    data.setTargetSkipRoots([secondRoot])
    assert project.projChanged is False
    assert data.targetLastCount == newWords - secondWords
    assert data.dailyProgress == writtenWords

    # Re-including the root restores the total, and progress is still
    # unaffected since none of its words were written this session
    project.setProjectChanged(False)
    data.setTargetSkipRoots([])
    assert project.projChanged is True
    assert data.targetSkipRoots == set()
    assert data.targetLastCount == newWords
    assert data.dailyProgress == writtenWords

    # Excluding an empty root is still a change in roots, but since it
    # has no words, the total and progress are untouched
    thirdRoot = project.newRoot(nwItemClass.NOVEL)
    project.setProjectChanged(False)
    data.setTargetSkipRoots([thirdRoot])
    assert project.projChanged is True
    assert data.targetSkipRoots == {thirdRoot}
    assert data.targetLastCount == newWords
    assert data.dailyProgress == writtenWords


@pytest.mark.core
def testProjectData_DailyTargetCurrent(monkeypatch, mockGUI):
    """Test the setInitDailyTarget setter. A stored reference count
    must only be restored when it was recorded on the same day; a count
    from any other day is stale and must be discarded so it cannot leak
    into today's progress calculation.
    """
    monkeypatch.setattr(projectdata, "date", _FakeDate)
    _FakeDate._today = date(2026, 7, 22)

    project = MockProject()
    data = ProjectData(project)  # type: ignore

    # A record from the same day is restored as-is
    data.setInitDailyTarget(60, "2026-07-22")
    assert data.dailyLastCount == 60
    assert data._dailyLastDate == date(2026, 7, 22)

    # A record from an earlier day is stale and discarded, and the date
    # is bumped to today so it isn't mistaken for a fresh record later
    data.setInitDailyTarget(100, "2026-07-20")
    assert data.dailyLastCount == 0
    assert data._dailyLastDate == date(2026, 7, 22)

    # A missing/invalid date is treated the same as a stale record
    data.setInitDailyTarget(100, None)
    assert data.dailyLastCount == 0
    assert data._dailyLastDate == date(2026, 7, 22)

    # End-to-end: a project file with a daily target set two days ago is
    # loaded. The stale count must not offset today's progress
    data = ProjectData(project)  # type: ignore
    data.setInitDailyTarget(100, "2026-07-20")
    data.setDailyProgress(0, 500)
    assert data.dailyProgress == 0


@pytest.mark.core
def testProjectData_DailyProgress(monkeypatch, mockGUI):
    """Test the setDailyProgress setter. The daily word count passed in
    is the cumulative session change since the project was last loaded,
    not the change since the previous call, so it must be combined with
    the carried-over daily baseline to survive across sessions on the
    same day, and be recalculated when the clock ticks over to a new day.
    """
    monkeypatch.setattr(projectdata, "date", _FakeDate)
    _FakeDate._today = date(2026, 7, 20)

    project = MockProject()
    data = ProjectData(project)  # type: ignore
    data.setProjectTarget(1000, None, False)

    # First update of a session with no prior daily record and nothing
    # written yet: the progress is zero, and the remaining word count is
    # the full target less what already existed at the start of the day
    data.setDailyProgress(0, 500)
    assert data.dailyProgress == 0
    assert data._remainingCount == 500

    # As the session progresses, the progress grows by the session word
    # count, but the remaining count for the day stays fixed
    data.setDailyProgress(60, 560)
    assert data.dailyProgress == 60
    assert data._remainingCount == 500

    # A new session is opened later the same day. The project file was
    # saved with the 60 words from the previous session already included
    # in the initial count, and the daily record ("last") carries the
    # 60-word progress forward
    data = ProjectData(project)  # type: ignore
    data.setProjectTarget(1000, None, False)
    data.setInitDailyTarget(60, "2026-07-20")

    # No new typing yet in this session, so progress should still read
    # 60, and the remaining count must match the earlier session, not
    # be reduced by the 60 words a second time
    data.setDailyProgress(0, 560)
    assert data.dailyProgress == 60
    assert data.dailyLastCount == 60
    assert data._remainingCount == 500

    # More words are added in the second session
    data.setDailyProgress(40, 600)
    assert data.dailyProgress == 100
    assert data._remainingCount == 500

    # The clock ticks over to the next day mid-session. Progress resets
    # for the new day, and the remaining count drops by the full amount
    # written the previous day (100 words). The session word count keeps
    # accumulating from the same session baseline, so 5 more words typed
    # after the rollover means 45 in total this session
    _FakeDate._today = date(2026, 7, 21)
    data.setDailyProgress(45, 605)
    assert data.dailyProgress == 5
    assert data._remainingCount == 400
    assert data._dailyLastDate == date(2026, 7, 21)

    # Further typing on the new day accumulates from the new baseline
    data.setDailyProgress(55, 615)
    assert data.dailyProgress == 15
    assert data._remainingCount == 400


@pytest.mark.core
def testProjectData_EffectiveDailyGoal(monkeypatch, mockGUI):
    """Test the getEffectiveDailyGoal getter. It must return the fixed
    daily goal unless automatic calculation is enabled, a deadline is
    set in the future, and there is a positive word count remaining.
    """
    monkeypatch.setattr(projectdata, "date", _FakeDate)
    _FakeDate._today = date(2026, 7, 20)

    project = MockProject()
    data = ProjectData(project)  # type: ignore
    data.setProjectTarget(1000, date(2026, 7, 24), False)
    data.setDailyProgress(0, 400)
    assert data._remainingCount == 600

    # With automatic calculation off, the fixed goal is always returned
    data.setDailyTarget(50, False)
    assert data.getEffectiveDailyGoal() == 50

    # With automatic calculation on and four full days plus today left
    # until the deadline, the remaining count is spread across all of them
    data.setDailyTarget(50, True)
    assert data.getEffectiveDailyGoal() == 600 // 5

    # When the deadline is today, all the remaining words are due today
    data.setProjectTarget(1000, date(2026, 7, 20), False)
    data.setDailyProgress(0, 400)
    assert data.getEffectiveDailyGoal() == 600

    # When the deadline has passed, fall back to the fixed daily goal
    data.setProjectTarget(1000, date(2026, 7, 19), False)
    data.setDailyProgress(0, 400)
    assert data.getEffectiveDailyGoal() == 50

    # When the remaining word count isn't positive, also fall back
    data.setProjectTarget(400, date(2026, 7, 24), False)
    data.setDailyProgress(0, 400)
    assert data._remainingCount == 0
    assert data.getEffectiveDailyGoal() == 50
