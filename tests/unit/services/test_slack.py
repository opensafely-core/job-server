from slack_sdk.errors import SlackApiError

from services import slack


def test_post(mocker):
    mock = mocker.patch("services.slack.client", autospec=True)

    slack.post("text", "channel")

    mock.chat_postMessage.assert_called_once_with(channel="channel", text="text")


def test_post_error(mocker, log_output):
    mock = mocker.patch("services.slack.client", autospec=True)

    mock.chat_postMessage.side_effect = SlackApiError(
        message="an error", response={"error": "an error occurred"}
    )

    slack.post("text", "channel")

    mock.chat_postMessage.assert_called_once_with(channel="channel", text="text")

    # check we logged the slack failure
    assert len(log_output.entries) == 1, log_output.entries
    assert log_output.entries[0] == {
        "channel": "channel",
        "exc_info": True,
        "event": "Failed to notify slack in channel: channel",
        "log_level": "error",
    }


def test_link():
    assert slack.link("url") == "<url>"
    assert slack.link("url", "text") == "<url|text>"
