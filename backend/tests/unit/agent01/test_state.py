from app.agent.agent01.state import clear_state, get_state


def test_get_state_returns_same_instance_for_same_inquiry() -> None:
    s1 = get_state(1)
    s1.case_notes.append({"content": "x"})
    s2 = get_state(1)

    assert s2.case_notes == [{"content": "x"}]

    clear_state(1)


def test_get_state_is_isolated_per_inquiry() -> None:
    a = get_state(101)
    b = get_state(102)
    a.case_notes.append({"content": "for-101"})

    assert b.case_notes == []

    clear_state(101)
    clear_state(102)


def test_clear_state_resets_to_fresh_instance() -> None:
    get_state(201).case_notes.append({"content": "x"})
    clear_state(201)

    assert get_state(201).case_notes == []

    clear_state(201)
