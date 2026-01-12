# ZZZ Drive Disk Salvaging Helper

This repository contains the scripts used to populate the build data used by the
[Zenless Zone Zero Drive Disk Salvaging Helper sheet](https://docs.google.com/spreadsheets/d/1ZIZa4zg0zkkPIP2TrHQaMw9XzjJLvO2iOpUAyREDFwY/edit).
Build data is scraped from https://www.prydwen.gg/zenless/characters and the corresponding agent build pages.

## Files
- scrape_prydwen.py: Scrapes Prydwen agent build data and outputs a `characters_output_{version}.json` file containing
recommended 4pc sets, 2pc sets, main stats, and substats for each character.
- drive_disk_salvaging_helper.ipynb: Notebook that processes the JSON output of the `scrape_prydwen.py` file and exports
a `drive_disk_salvaging_helper_{version}.csv` file that can be imported into the Prydwen Builds tab of the spreadsheet.

## Updating the sheet
1. Use `uv sync` to install any required dependencies
2. Run all the cells in the `drive_disk_salvaging_helper.ipynb` notebook
3. Import the generated `drive_disk_salvaging_helper_{version}.csv` into the Prydwen Builds tab of the spreadsheet
4. If new sets have been added to the game since the sheet was last updated, add appropriate rows to the `Set+Main`,
`Set+Sub`, `Set Overview`, and `Find-Helper` tabs
