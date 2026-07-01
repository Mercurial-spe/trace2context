from trace2context.agent.model import _extract_responses_text


def test_extract_responses_text_from_output_parts():
    data = {
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": "hello",
                    }
                ],
            }
        ]
    }

    assert _extract_responses_text(data) == "hello"


def test_extract_responses_text_prefers_top_level_output_text():
    assert _extract_responses_text({"output_text": "top-level", "output": []}) == "top-level"
