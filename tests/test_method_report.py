"""The write-in method report: which methods entries use that the form's dropdown does not offer."""
import method_report


def test_write_ins_are_methods_not_in_the_dropdown_counted_by_entry():
    entries = [["sae", "custom-probe"], ["custom-probe", "reward-modeling"], ["sae"]]
    rows = method_report.write_ins(entries, options=["sae", "linear-probing"])
    assert rows == [("custom-probe", 2), ("reward-modeling", 1)]


def test_a_write_in_used_by_two_or_more_entries_is_ready_to_add():
    rows = [("custom-probe", 2), ("reward-modeling", 1)]
    assert method_report.ready_to_add(rows) == ["custom-probe"]


def test_a_method_repeated_within_one_entry_counts_once():
    rows = method_report.write_ins([["custom-probe", "custom-probe"]], options=[])
    assert rows == [("custom-probe", 1)]


def test_the_real_wiki_and_form_produce_a_report(capsys):
    assert method_report.main([]) == 0
    out = capsys.readouterr().out
    assert "write-in" in out.lower()
