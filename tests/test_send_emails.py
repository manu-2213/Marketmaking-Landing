import csv
import smtplib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import send_emails_from_csv as sender


class SendEmailsTests(unittest.TestCase):
    def run_main(self, csv_path, smtp, answer="yes"):
        with patch.object(sender.smtplib, "SMTP", smtp), patch.object(
            sender, "DRY_RUN", False
        ), patch.object(sender, "SECONDS_BETWEEN_EMAILS", 0), patch(
            "sys.argv", ["send", str(csv_path)]
        ), patch.dict("os.environ", {"GMAIL_APP_PASSWORD": "abcd efgh ijkl mnop"}), patch(
            "builtins.input", return_value=answer
        ), patch("builtins.print"):
            sender.main()

    def make_csv(self, directory, *emails):
        path = Path(directory) / "batch.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, ["recipient_email", "recipient_name", "subject", "body"])
            writer.writeheader()
            for email in emails:
                writer.writerow(dict(recipient_email=email, recipient_name="N", subject="S", body="£8 body"))
        return path

    def test_bad_login_stops_after_one_attempt_and_sends_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.make_csv(d, "a@x.edu", "b@x.edu", "c@x.edu")
            smtp = MagicMock()
            smtp.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad")
            with self.assertRaises(SystemExit):
                self.run_main(path, smtp)
            self.assertEqual(smtp.return_value.login.call_count, 1)
            smtp.return_value.sendmail.assert_not_called()
            self.assertFalse(Path(f"{path}.sent").exists())

    def test_password_spaces_are_removed_and_one_login_covers_the_batch(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.make_csv(d, "a@x.edu", "b@x.edu")
            smtp = MagicMock()
            self.run_main(path, smtp)
            smtp.return_value.login.assert_called_once_with(sender.SENDER_EMAIL, "abcdefghijklmnop")
            self.assertEqual(smtp.return_value.sendmail.call_count, 2)

    def test_rerun_skips_addresses_already_sent(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.make_csv(d, "a@x.edu", "b@x.edu")
            smtp = MagicMock()
            smtp.return_value.sendmail.side_effect = [None, smtplib.SMTPResponseException(421, b"limit")]
            self.run_main(path, smtp)
            self.assertEqual(Path(f"{path}.sent").read_text().split(), ["a@x.edu"])

            retry = MagicMock()
            self.run_main(path, retry)
            retry.return_value.sendmail.assert_called_once()
            self.assertEqual(retry.return_value.sendmail.call_args.args[1], "b@x.edu")

    def test_refused_address_does_not_stop_the_batch(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.make_csv(d, "bad@x.edu", "ok@x.edu")
            smtp = MagicMock()
            smtp.return_value.sendmail.side_effect = [
                smtplib.SMTPRecipientsRefused({"bad@x.edu": (550, b"no")}), None,
            ]
            self.run_main(path, smtp)
            self.assertEqual(Path(f"{path}.sent").read_text().split(), ["ok@x.edu"])

    def test_declining_confirmation_sends_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.make_csv(d, "a@x.edu")
            smtp = MagicMock()
            with self.assertRaises(SystemExit):
                self.run_main(path, smtp, answer="no")
            smtp.return_value.sendmail.assert_not_called()


if __name__ == "__main__":
    unittest.main()
