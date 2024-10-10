# Configuration (config.json)

The config.json is made of threee main sections: [profiles](#profiles), [export](#export), and [cheatsheet](#cheatsheet)

If you don't have a config.json, make sure that you have ran the `first_time_setup.py` script prior to doing anything here

## <a name="profiles"></a> Profiles
An example profiles config element:
```
"profiles": {
    "defualt": {
        "profile_path": "C:\\Users\\xxxx\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\abcdef.default-release",
        "provided_email": "a@a.com"
    }
}
```

The individual profiles are parsed as such:
```
"Profile Name": {
    "profile_path": "Directory for the firefox profile" // type: str
    "provided_email": "An email for form filling" // type: str
}
```

## <a name="export"></a> Export
An example export config element:
```
"export": {
    "on_error": "all", // Recomended
    "on_compleation": "scored", // Recomended
    "export_dir": "forms/", // Recomended
}
```

There are multiple export modes:
 - All: Will export all awnsers, including unscored questions like name entries.
 - Scored: Will only all scored awnsers.
 - Empty: Will only export the questions without an awnser key.
 - None: Will not export.
 - Ask: Will prompt user at export time.


the export config is parsed as such.
```
"export": {
    "on_error": "export mode", // type: export_mode(str)
    "on_compleation": "export mode", // type: export_mode(str)
    "export_dir": "directory to store .forms" // type: str // it will make this directory if it doens't exist at export time.
}
```

Note: if cheatsheet is enabled and is sending forms to servers, it will automaticly stip the form in the "scored" mode, prior to sending.

## <a name="cheatsheet"></a> Cheatsheet
There are three ways to deactivate networking features:
 - if `cheatsheet.py` is missing (can't be imported.)
 - if there is no `"cheatsheet"` element in config.json
 - or `"enabled"` inside of the cheatsheet element in config.json is `false`

An example cheatsheet config element:
```
"cheatsheet": {
    "enabled": true, // recomended
    "send_forms": true, // recomended
    "recv_forms": true, // recomended
    "providers": [
        {
            "name": "localhost",
            "mode": "ipv4",
            "addr": "127.7.7.7",
            "port": 6590 // recomended
        }
    ],
    "hosting": [
        {
            "name": "localhost",
            "mode": "ipv4",
            "addr": "127.7.7.7",
            "port": 6590, // recomended
            "form_directory": "forms/" // recomended to be whatever export's 'export_dir' is 
        }
    ]
}
```

There are many componets to this config element:
 - enabled: If this is false, no calls to cheatsheet will be made
 - recv_forms: If you don't have the form in your export's 'export_dir' is cheatsheet will send a request to all of your providers for the form.
 - send_forms: When you completed with 100% score, you will contribute your form to your providers.
 - providers: These are the servers that you request forms from (Say that ten times fast).
 - hosting: These are the configurations for when you decide to host a cheatsheet server locally, this can be done by running `cheatsheet.py` instead of `main.py` and following the cli instructions.

In both `providers` and `hosting`, there is an value called `mode` it is the type of interface the server is on:
 - ipv4: Standard ipv4 Networking (tcp)
 - ipv6: Standard ipv6 Networking (tcp)
 - blue: Networking over bluetooth (tcp)

A provider is defined as Such
```
{
    "name": "Provider Name", // type: str
    "mode": "Server mode", // type: server_mode(str)
    "addr": "Server address", // type: str
    "port": 6590 // type: int
}
```

A hosting config is nearly idendtical to a provider but with `form_directory`
```
{
    "name": "Provider Name", // type: str
    "mode": "Server mode", // type: server_mode(str)
    "addr": "Server address", // type: str
    "port": 6590, // type: int
    "form_directory": "directory where forms are stored/" // type: str, must end in /
}
```

## Whole example config.json
```
{
    "profiles": {
        "defualt": {
            "profile_path": "C:\\Users\\xxxx\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\abcdef.default-release",
            "provided_email": "a@a.com"
        }
    },
    "export": {
        "on_error": "all",
        "on_compleation": "scored",
        "export_dir": "forms/"
    },
    "cheatsheet": {
        "enabled": true,
        "send_forms": true,
        "recv_forms": true,
        "providers": [
            {
                "name": "localhost",
                "mode": "ipv4",
                "addr": "127.7.7.7",
                "port": 6590
            }
        ],
        "hosting": [
            {
                "name": "localhost",
                "mode": "ipv4",
                "addr": "127.7.7.7",
                "port": 6590,
                "form_directory": "forms/"
            }
        ]
        
    }
}
```