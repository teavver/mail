## mail automation tool

match incoming/existing messages against regex patterns and execute local scripts

## installation

0. `git clone https://github.com/teavver/mail && cd mail`
1. `uv venv`
2. `. .venv/bin/activate`
3. `uv pip install -e .`
4. or full (development): `uv pip install -e .[testing,linting]`

## how to get imap host and app password for email

gmail:
- https://accounts.google.com/v3/signin/challenge/pwd?continue=https://myaccount.google.com/apppasswords&service=accountsettings
- host: `imap.gmail.com`

icloud
- https://support.apple.com/en-us/102654
- host: `imap.mail.me.com`

## script mode

- `polling` = will continuously check for new messages and check against script config
- `history` = fetch `fetch_limit` existing messages and match

## example config.toml

it is recommended to load `login` and `password` from .env instead of config.toml

.env with `LOGIN` and `PASSWORD`, values have priority over config.toml credentials

```toml
[general]
run_mode = "all" # all | history | polling (default = all)
# when 'all', history scripts are executed first, then polling
# single mode run_mode will ignore any scripts not matching run_mode from config
fetch_limit = 100 # how many msgs to fetch in history mode (default = 50)
polling_interval = 5 # check for new msgs every N seconds (default = 5)
polling_timeout = 240 # quit after N seconds, regardless of matches. 0 for no timeout (default = 0)

[mail]
login = "me@gmail.com"
password = "XXXX XXXX XXXX XXXX"
host = "imap.gmail.com"
port = 993

[[scripts]]
name = "example 1"
mode = "history"
exec_once = true # call the script once, on first match, then ignore every next match (persistent)
exec_path = "python3 /Users/USER/some_script.py --debug"
regexp_main = "Google" # your regex (default = ".*")
regexp_main_target = "title" # match regexp_main against email title (subject) (default = title)

[[scripts]]
name = "example 2"
mode = "polling"
exec_once = false
exec_path = "node /Users/USER/test.js"
regexp_from = "noreply@steampowered.com" # match only if this address sent the message
regexp_main = "Sold"
regexp_main_target = "body" # match regexp_main against body
pipe_html = true # forward the mail's content (html) to my script
```

## args

see `--help` for details

| arg name            | default value | description                                                                                                                                                                               |
|---------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -d --debug          | False         | debug logs; affects only term output                                                                                                                                                                  |
| -q --quiet          | False         | no logs except errors; affects only term output                                                                                                                                                                  |
| -s --slow           | False         | disable bulk option when fetching existing emails (history mode). the imap-tools will fetch messages one by one; much lower memory consumption, but significantly slower than normal mode |
| -lf --logfile       | None          | provide custom path to your logfile, if you don't want to use the default logs.txt one                                                                                                    |
| -cc --custom-config | None          | provide path to a valid config.toml file to use instead of the local one. useful when calling this tool from other automation tools, e.g. cron                                            |
| -fm --force-mode    | None          | override the app run mode defined in your config                                                                                                                                          |