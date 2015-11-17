# TPLink Harvest
Harvest TP-Link Firmware Files


## Enumerate models
<img src='TPLink_1.png'>
```python
models= driver.find_elements_by_css_selector('.list ul li span a')
```

## Enumerate files
<img src='TPLink_2.png'>
```python
# choose support type='Firmware'
In [15]: CSSs('ul.row li a')[1].text
Out[15]: 'Firmware'

In [16]: CSSs('ul.row li a')[1].click()

# basic-info, split by '\n' newline
In [19]: CSSs('#content_firmware table')[0].find_element_by_css_selector('tr.basic-info').text
Out[19]: 'Archer_C2(UN)_v1_151022\nPublished Date\n22/10/15\nLanguage\nEnglish\nFile Size\n6.56 MB'

In [20]: print(_19)
Archer_C2(UN)_v1_151022
Published Date
22/10/15
Language
English
File Size
6.56 MB

# first more-info
In [21]: CSSs('#content_firmware table')[0].find_element_by_css_selector('tr.more-info').text
Out[21]: 'Modifications and Bug Fixes\nNew Features/Enhancement：\n 1.Improved the PPPOE function.\n2.Optimized the display on Tether APP.\n 3.Added an option which allo ws ping packet from WAN port in "Security".\n 4.Optimized the performance of web server and fixed some web display bugs on IE8.\nBug Fixed：\n1.Fixed the bug that media player will detect MP4 file as music file when Media server is enabled.\n 2.Fixed the bug that can\'t use DMZ_Loopback function in PPPOE mode.\n3.Fixed the bug that UK BT customers cant watch IPTV in PPPOE mode.'


# second more-info
In [24]: CSSs('#content_firmware table')[0].find_elements_by_css_selector('tr.more-info')[1].text
Out[24]: "Notes\n1.For Archer C2(UN)_V1\n2. Old firmware’s configuration file can be imported into this new firmware.\n3. Your device’s configuration won't be lost aer upgrading, which means you don't need to configure your device again."

# productName
In [50]: CSS('a.a strong').text
Out[50]: 'AC750 Wireless Dual Band Gigabit Router'

# download_url
In [31]: CSSs('#content_firmware table')[0].find_element_by_css_selector('a').get_attribute('href')
Out[31]: 'http://www.tp-link.com/res/down/soft/Archer_C2(UN)_v1_151022.zip'

# Table0 is displayed
In [47]: CSSs('#content_firmware table')[0].is_displayed()
Out[47]: True

# Table[4] is not displayed
In [48]: CSSs('#content_firmware table')[3].is_displayed()
Out[48]: False

```

## Revision Select
Below is a Twitter Bootstrap style Dropdown list, not a HTML Select. Selenium Select is unable to select it. We have to click on this control so as to make hidden items ('#dlDropDownBox dd ul li a') visible.
<img src='TPLink_3.png'>
<img src='TPLink_3_1.png'>
```python
In [138]: CSS('#dlDropDownBox > dd:nth-child(2) > p:nth-child(1) > span:nth-child(1)').click()

In [139]: [_.text for _ in CSSs('#dlDropDownBox dd ul li a')]
Out[139]: ['V3', 'V2', 'V1']

In [140]: CSSs('#dlDropDownBox dd ul li a')[2].text
Out[140]: 'V1'

In [141]: CSSs('#dlDropDownBox dd ul li a')[2].click()

In [142]: driver.current_url
Out[142]: 'http://www.tp-link.com/en/download/TL-MR3420_V1.html'

```
