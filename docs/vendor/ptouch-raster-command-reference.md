<!-- Converted from ptouch-raster-command-reference.pdf. Provenance: see INDEX.md -->

Software Developer's Manual
Raster Command Reference
PT-P900/P900W/P950NW/P910BT
Version 1.02
The Brother logo is a registered trademark of Brother Industries, Ltd.
Brother is a registered trademark of Brother Industries, Ltd.
© 2020 Brother Industries, Ltd. All rights reserved.


Microsoft and Windows are registered trademarks of Microsoft Corporation in the United States and other
countries.


Each owner whose software title is mentioned in this document has a Software License Agreement specific to
its proprietary programs.
Any trade names and product names of companies appearing on Brother products, related documents and
any other materials are all trademarks or registered trademarks of those respective companies.
IMPORTANT - PLEASE READ CAREFULLY

Note

This documentation (“Documentation”) provides information that will assist you in controlling your Printer PT-
XXXX (where “XXXX” is the model name).
You may use the Documentation only if you first agree to the following conditions.
If you do not agree to the following conditions, you may not use the Documentation.




Condition of Use

You may use and reproduce the Documentation to the extent necessary for your own use of your Printer Model
(“Purpose”). Unless expressly permitted in the Documentation, you may not;
(i) copy or reproduce the Documentation for any purpose other than the Purpose,
(ii) modify, translate or adapt the Documentation, and/or redistribute it to any third party,

(iii) rent or lease the Documentation to any third party, or,

(iv) remove or alter any copyright notices or proprietary rights legends included within the Documentation.




No Warranty

a. Any updates, upgrades or alteration of the Documentation or Printer Model will be performed at the sole
   discretion of Brother. Brother may not respond to any request or inquiry about the Documentation.

b. THIS DOCUMENTATION IS PROVIDED TO YOU "AS IS" WITHOUT WARRANTY OF ANY KIND,
   WHETHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTY
   OF FITNESS FOR A PARTICULAR PURPOSE.                  BROTHER DOES NOT REPRESENT OR WARRANT
   THAT THIS DOCUMENTATION IS FREE FROM ERRORS OR DEFECTS.

c. IN NO EVENT SHALL BROTHER BE LIABLE FOR ANY DIRECT, INDIRECT, PUNITIVE, INCIDENTAL,
   SPECIAL OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER, ARISING OUT OF
   THE USE, INABILITY TO USE, OR THE RESULTS OF USE OF THE DOCUMENTATION OR ANY
   SOFTWARE PROGRAM OR APPLICATION YOU DEVELOPED IN ACCORDANCE WITH THE
   DOCUMENTATION.
                                                                                                                                 Raster Command Reference




                                                              Contents

Introduction ······························································································ 1
About Raster Commands ············································································ 2
1. Printing Using Raster Commands ····························································· 3
2. Print Data ······························································································ 5
     2.1 Print data overview ························································································ 5

     2.2 Sample (analyzing the print data of the test page) ················································ 7
           2.2.1 Preparation ........................................................................................................... 7
           2.2.2 Checking the print data......................................................................................... 7
           2.2.3 Explanation of print data for the test page .......................................................... 10
     2.3 Page data details ························································································· 12
           2.3.1 Resolution .......................................................................................................... 12
           2.3.2 Page size ............................................................................................................ 13
           2.3.3 Feed amount ...................................................................................................... 17
           2.3.4 Maximum and minimum lengths ......................................................................... 18
           2.3.5 Raster line .......................................................................................................... 19
3. Print Command List ··············································································· 22
4. Printing Command Details ······································································ 23
           NULL            Invalidate ................................................................................................... 23
           ESC @           Initialize...................................................................................................... 23
           ESC i S         Status information request ......................................................................... 23
           ESC i a         Switch dynamic command mode ............................................................... 32
           ESC i z         Print information command ........................................................................ 33
           ESC i M         Various mode settings ............................................................................... 35
           ESC i K         Advanced mode settings ........................................................................... 36
           ESC i d         Specify margin amount (feed amount) ....................................................... 37
           ESC i A         Specify the page number in “cut each * labels” ......................................... 37
           M               Select compression mode ......................................................................... 38
           G               Raster graphics transfer ............................................................................ 40
           Z               Zero raster graphics................................................................................... 40
           FF              Print command........................................................................................... 40
           Control-Z       Print command with feeding ...................................................................... 41
           ESC i !         Specify automatic status notification mode ................................................ 41
5. Flow Charts ·························································································· 42
     5.1 Concurrent printing normal flow for USB connection ············································ 43

     5.2 Concurrent printing error flow for USB connection (when feeding at the end of the page)44

     5.3 Concurrent printing error flow for USB connection (with a concurrent printing error such

     as end of tape) ·································································································· 45

     5.4 Buffered printing normal flow for USB/Bluetooth connection ·································· 46

     5.5 Buffered printing error flow for USB/Bluetooth connection ····································· 47

     5.6 Normal Flow for Network (Standard TCP/IP port) Connection ································ 48
Appendix A: USB Specifications ································································· 49
Appendix B: Introducing the Brother Developer Center ·································· 50




                                                                   - i -
                                                                                           Raster Command Reference




Introduction
This material provides the necessary information for directly controlling the Brother printer PT-XXXX (where
“XXXX” is the model name).
This information is provided assuming that the user has full understanding of the operating system being used
and basic mastery of USB in a developer's environment.
Details concerning the USB interface are not described in this material. If a USB interface is being used, refer
to “Appendix A: USB Specifications” to prepare the interface.




Read the model names that appear in the screens in this manual as the name of your printer.




                                                     - 1 -
                                                                                                    Introduction
                                                                                         Raster Command Reference




About Raster Commands
Using raster commands an PT-XXXX printer (where “XXXX” is the model name) can be used to print without
using our printer driver.
This operation is useful in the following situations.
⚫ When printing from an operating system other than Windows
    (Example: When printing from a Linux computer or mobile terminal)
⚫ When adding print functions to an existing system
In addition, printing can be performed with advanced settings.


In this material, “raster” refers to binary bitmap data (collection of dots).
Refer to this material to print by sending initialization commands and control codes together with raster data
to the PT-XXXX printer (hereafter, referred to as “printer”).
This manual describes the procedure for adding these codes and sending the data.




                                                        - 2 -
                                                                                    About Raster Commands
                                                                                               Raster Command Reference




1. Printing Using Raster Commands
The printing procedure is described below. For detailed flow charts, refer to “5. Flow Charts”. For details on
each command, refer to “4. Printing Command Details”.



   (1) Open the port



                         Port

                                (2) Send the status
                                (Confirm the printer status.)




                                                                                                              At your side
                                 (プリンタの状態を確認)



                                (3) Send the print data




                                (5) Send the status
                                (Confirm that printing is completed.)

    Computer, mobile
    terminal, etc.                                                       Your printer




                                                                                                  (4) Print

    (6) Close the port




                                                                 - 3 -
                                                                                 1. Printing Using Raster Commands
                                                                                            Raster Command Reference




(1) Open the USB/network/Bluetooth port
   Open the USB/network/Bluetooth port in the operating environment. The procedure for opening the
   USB/network/Bluetooth port is not described in this material.


(2) Confirm the printer status sent from the printer
   The “status information request” command is sent to the printer, the status information received from the
   printer is analyzed, and then the status of the printer is determined.
   For details on the “status information request” command and on the definitions of “status”, refer to “Status
   information request” in “4. Printing Command Details”.


(3) Send the print data
   If the status analysis confirms that media compatible with the print data is loaded into the printer and that
   no error has occurred, the print data is sent.
   The structure of the print data is explained in the next section, “2. Print Data”.
   Note:
   No command can be sent to the printer after the print data is transmitted and until the completion
   of printing is confirmed.
   Even the “status information request” command cannot be sent during printing.


(4) Print the data


(5) Confirm that printing is completed
   When printing is completed, the status is received from the printer.
   If this status is analyzed to confirm that printing is completed, printing one page is considered finished.
   If the print job has multiple pages, (2) through (4) are repeated.


(6) Close the USB/network/Bluetooth port
   After all printing is finished, close the USB/network/Bluetooth port.


   Note:
   In order to print at high speed when a USB port is used to send uncompressed raster data, the
   Brother PT-XXXX starts printing when it starts to receive print data, instead of waiting for a print
   command (concurrent printing).
   For the processing flow, for example when managing errors, refer to “5. Flow Charts”.




                                                       - 4 -
                                                                            1. Printing Using Raster Commands
                                                                                              Raster Command Reference




1. Print Data

2.1 Print data overview

The print data is constructed of the following: (1) Initialization commands, (2) Control codes, (3) Raster data,
and (4) Print commands. If the print job consists of multiple pages, (2) through (4) are repeated.


(1) Initialization commands
   Specified only once at the beginning of the job.
       Sequence       Command Name                                      Description/Example

                                            Sends a 200-byte invalidate command, and then resets the
            1        Invalidate
                                            printer to the receiving state.

                                            Initializes for printing.
            2        Initialize
                                            1Bh, 40h (Fixed)


(2) Control codes
   Added at the beginning of each page and sent for each page.
       Sequence       Command Name                                      Description/Example

                     Switch dynamic         Switches the printer to raster mode.
            1
                     command mode           1Bh, 69h, 61h, 01h

                     Specify automatic
                                            Dynamically switches whether an automatic status notification is
                     status notification
            2                               given during printing.
                     mode
                                            1Bh, 69h, 21h, 00h
                     (PT-P910BT only)

                                            Sets the print information for the printer.
                     Print information      When printing 100 mm on 24-mm-wide tape with the 180 dpi
            3
                     command                model:
                                            1Bh, 69h, 7Ah, 84h, 00h, 18h, 00h, 9Ch, 02h, 00h, 00h, 00h, 00h

                     Various mode           When auto cut is enabled:
            4
                     settings               1Bh, 69h, 4Dh, 40h

                                            When an auto cut setting is effective, specify the number of
                     Specify the page       sheets for auto cut.
            5        number in “cut
                     each * labels”         For auto cut every single sheet,
                                            1Bh, 69h, 41h, 01h

                     Advanced mode          When half cut is enabled, and chain printing is disabled:
            6
                     settings               1Bh, 69h, 4Bh, 0Ch

                                            Specifies the amount of the margins.
                     Specify margin
            7                               For 1 mm margins on the 360 dpi model:
                     amount
                                            1Bh, 69h, 64h, 0Eh, 00h

                                            Selects the compression mode for raster graphics.
                     Select compression
            8                               To send the data compressed to TIFF format:
                     mode
                                            4Dh, 02h


                                                      - 5 -
                                                                                                       2. Print Data
                                                                                             Raster Command Reference




(3) Raster data
   Repeated for each page in the print job.
       Sequence       Command Name                                  Description/Example

                     Raster graphics
           -                                  Sends a raster line that contains data with pixels set to “ON”.
                     transfer

                                              Sends a raster line with all pixels set to “0”. (Valid only when
           -         Zero raster graphics     TIFF is selected as the compression mode)
                                              5Ah (Fixed)


(4) Print commands
   Specified at the end of the page.
       Sequence       Command Name                                  Description/Example

                                              Specifies at the end of a page that is not the last page.
           -         Print command
                                              0Ch（Fixed）

                     Print command with       Specifies at the end of the last page.
           -
                     feeding                  1Ah (Fixed)




                                                      - 6 -
                                                                                                      2. Print Data
                                                                                               Raster Command Reference




2.2 Sample (analyzing the print data of the test page)

The print data created by the printer driver is described here.
As an example, we will check the print data created when the [Print Test Page] button in the printer Properties
dialog box is clicked to print the test page.
Since the print data differs depending on the print settings of the printer, refer to this procedure and try creating
print data with various print settings.
Furthermore, this procedure is for the Windows ® 10 operating environment. A similar procedure can be
performed if you are using a different operating system.




                                                  Print Properties

2.2.1 Preparation

Install the two listed below.
・ Printer driver of the Brother PT-XXXX
・ Binary file editor
The data that we will analyze in this sample is a binary file.
Therefore, use a binary file editor to display and check the contents of the binary file.



2.2.2 Checking the print data

The procedure for checking the print data is provided below.
      Step 1: Change the port of the printer to “FILE:”.
      Step 2: Print the desired item (in this case, the test page), and then specify the file name.
      Step 3: Open the created file in the binary file editor to check it.




                                                       - 7 -
                                                                                                        2. Print Data
                                                                                         Raster Command Reference




Step 1: Change the port of the printer to “FILE:”.
  Open the Printers and Faxes folder, and then right-click the printer to display the Properties dialog box.
  In the Properties dialog box, click the [Ports] tab, select the “FILE:” check box, and then click the [Apply]
  button.




                             [Ports] tab of the printer Properties dialog box


Step 2: Print the item (in this case, the test page), and then specify the file name.
  Print the test page with “36mm” selected as the paper size in the print settings.




                                                  - 8 -
                                                                                                  2. Print Data
                                                                                        Raster Command Reference




  When the test page is printed with the printer, a dialog box appears so that the file name can be specified.
  (Refer to the illustration below.)
  After a file name is typed in and the [OK] button is clicked, the printer driver creates the print data and
  saves it in a file with the specified name.




                                          Save Print Output As


Step 3: Open the print data in the binary file editor.
  Open the saved file in the binary file editor. The rows of numbers that appear are the print data. (Refer
  to the illustration below.)
  The print data is constructed of the following: (1) Initialization commands, (2) Control codes, (3) Raster
  data and (4) Print commands, which were described in “2.1 Print data overview”. For details on the print
  data, refer to “2.2.3 Explanation of print data for the test page”.




                                                Print data



                                                   - 9 -
                                                                                                 2. Print Data
                                                                                           Raster Command Reference




2.2.3 Explanation of print data for the test page

The print data for the test page outputted in the previous section is described below.
The following illustration shows the print data created in section “2.2.1 Preparation” opened in the binary file
editor.




                                                   Print data




                                                    - 10 -
                                                                                                    2. Print Data
                                                                                           Raster Command Reference




Descriptions for the numbers in the print data on the previous page are provided in the following table.
For details on each command, refer to “4. Printing Command Details”.


         No.         Command Name                                       Description

          １       Invalidate                 A 200-byte invalidate command is sent.

          2       Initialize                 The “initialize” command is sent.

                  Switch dynamic             The printer is switched to raster mode.
          3
                  command mode               Send this command before sending raster data to the printer.

                                             Internal specification commands
                  Job ID setting             Since this is a command for outputting with the commercial
          4
                  commands                   version driver, it is unnecessary for the user to send this
                                             command.

                  Print information          Media size information for the print data is sent.
          5
                  command                    This is the command for “36 mm” tape.

                  Various mode settings      This is a command for specifying a mode.
          6
                  (1Bh+69h+4Dh+40h)          Here, automatically cutting is specified.

                  Specify the page
                                             The number of pages printed before automatically cutting is
          7       number in “cut each *
                                             specified.
                  labels”

                                             This is the command for specifying settings for the advanced
                  Advanced mode              mode.
          8
                  settings                   In this case, “no chain printing” is enabled, and “half cut” is
                                             enabled.

                                             Internal specification commands
                  Specify number of          Since this is a command for outputting with the commercial
          9
                  copies                     version driver, it is unnecessary for the user to send this
                                             command.

                                             Specifies the amount of the margins.
          10      Specify margin amount
                                             This is the command for “14 dots”.

                  Select compression
          11                                 TIFF compression mode is selected.
                  mode

          12      Raster data                Raster data continues.

                  Print command with         Since it is the last page, the print command with feeding is sent
          13
                  feeding                    at the end of the page.




                                                    - 11 -
                                                                                                    2. Print Data
                                                                          Raster Command Reference




2.3 Page data details

2.3.1 Resolution

   PT-P900/P900W/P950NW
                         Resolution                      Height-to-Width Proportion

                   360 dpi high, 360 dpi wide                       1:1

                   360 dpi high, 720 dpi wide                       1:2


   PT-P910BT
                         Resolution                      Height-to-Width Proportion

                   360 dpi high, 360 dpi wide                       1:1




                                                - 12 -
                                                                                   2. Print Data
                                                                                                    Raster Command Reference




2.3.2 Page size

     (a) Continuous length tape




                                             2
                       6                     4
            5


      1         3                          Print area




                             Feeding direction
                                      Landscape


     Number             1 Width                                                 2 Length
                        3 Print area width (maximum printing width)             4 Print area length
                        5 Width offset                                          6 Length offset
     TZe tape
          ID        Tape Size     Designation           1              2         3            4           5            6

                                  3.5 mm           3.38 mm                 3.38 mm                    0.00 mm
          263       3.5 mm                                       →2.3.4                    →2.3.4                  →2.3.3
                                  0.13"            48 dots                 48 dots                    0 dots

                                  6 mm             6.00 mm                 4.52 mm                    0.74 mm
          257       6 mm                                         →2.3.4                    →2.3.4                  →2.3.3
                                  0.23"            84 dots                 64 dots                    10 dots

                                  9 mm             9.00mm                  7.48 mm                    0.76 mm
          258       9 mm                                         →2.3.4                    →2.3.4                  →2.3.3
                                  0.35”            128 dots                106 dots                   11 dots

                                  12 mm            12.0 mm                 10.58 mm                   0.71 mm
          259       12 mm                                        →2.3.4                    →2.3.4                  →2.3.3
                                  0.47”            170 dots                150 dots                   10 dots

                                  18 mm            18.01 mm                16.51 mm                   0.75 mm
          260       18 mm                                        →2.3.4                    →2.3.4                  →2.3.3
                                  0.70”            256 dots                234 dots                   11 dots

                                  24 mm            24.00 mm                22.58 mm                   0.71 mm
          261       24 mm                                        →2.3.4                    →2.3.4                  →2.3.3
                                  0.94”            340 dots                320 dots                   10 dots

                                  36 mm            36.09 mm                32.03 mm                   2.03 mm
          262       36 mm                                        →2.3.4                    →2.3.4                  →2.3.3
                                  1.4”             512 dots                454 dots                   29 dots




                                                              - 13 -
                                                                                                              2. Print Data
                                                                                   Raster Command Reference




Heat-Shrink Tube
   ID    Tape Size    Designation        1              2         3          4           5            6

                      HS 5.8mm      5.60 mm                 3.95 mm                 0.85 mm
  415    HS 5.8 mm                                →2.3.4                 →2.3.4                   →2.3.3
                      HS 0.23"      80 dots                 56 dots                 12 dots

                      HS 8.8mm      8.70 mm                 6.77 mm                 1.00 mm
  416    HS 8.8 mm                                →2.3.4                 →2.3.4                   →2.3.3
                      HS 0.34”      124 dots                96 dots                 14 dots

                      HS 11.7mm     11.6 mm                 9.31 mm                 1.10 mm
  417    HS 11.7 mm                               →2.3.4                 →2.3.4                   →2.3.3
                      HS 0.46”      164 dots                132 dots                16 dots

                      HS 17.7mm     17.8 mm                 14.96 mm                1.40 mm
  418    HS 17.7 mm                               →2.3.4                 →2.3.4                   →2.3.3
                      HS 0.69”      252 dots                212 dots                20 dots

                      HS 23.6mm     23.7 mm                 18.06 mm                2.80 mm
  419    HS 23.6 mm                               →2.3.4                 →2.3.4                   →2.3.3
                      HS 0.93”      336 dots                256 dots                40 dots

                      HS 5.2 mm     5.2 mm        →2.3.4    2.82 mm      →2.3.4     1.20 mm       →2.3.3
  420    HS 5.2 mm
                      HS 0.20”      74 dots                 40 dots                 17 dots


                      HS 9.0 mmm    9 mm          →2.3.4    6.21 mm      →2.3.4     1.41 mm       →2.3.3
  421    HS 9.0 ㎜
                      HS 0.35”      128 dots                88 dots                 20 dots


                      HS 11.2 mm    11.3 mm       →2.3.4    7.06 mm      →2.3.4     2.12 mm       →2.3.3
  422    HS 11.2 mm
                      HS 0.44”      160 dots                100 dots                30 dots


                      HS 21 mm      21.0 mm       →2.3.4    16.93 mm     →2.3.4     2.05 mm       →2.3.3
  423    HS 21 mm
                      HS 0.82”      298 dots                240 dots                29 dots


                      HS 31.0 mm    31.0 mm       →2.3.4    25.40 mm     →2.3.4     2.82 mm       →2.3.3
  424    HS 31 mm
                      HS 1.2”       440 dots                360 dots                40 dots



NOTE: Hereafter, ID 415 to 419 is referred to as HS 2:1 and ID 420 to 424 is referred to as HS 3:1.




                                               - 14 -
                                                                                             2. Print Data
                                                                                         Raster Command Reference




(b) Split size




Number           1 Width                                           2 Length
                 3 Print area width (maximum printing width)       4 Print area length
                 5 Width offset                                    6 Length offset
                 7 Overall width                                   8 Width of overall print area
TZe tape
   ID      Tape      Designation       1          3            5                  7                       8
           Size                                                     [3] x Split number + [5] x 2     [3] x Split
                                                                                                      number

   279   12 mm       12 mm x 2     12.00 mm   11.99 mm   0.00 mm   12.00 mm x 2 + 0.00 mm x 2       12.00 mm x 2
                     0.47” x 2     170 dots   170 dots   0 dots    170 dots x 2 + 0 dots x 2        170 dots x 2

   285   12 mm       12 mm x 3     12.00 mm   11.99 mm   0.00 mm   12.00 mm x 3 + 0.00 mm x 2       12.00 mm x 3
                     0.47” x 3     170 dots   170 dots   0 dots    170 dots x 3 + 0 dots x 2        70 dots x 3

   291   12 mm       12 mm x 4     12.00 mm   11.99 mm   0.00 mm   12.00 mm x 4 + 0.00 mm x 2       12.00 mm x 4
                     0.47” x 4     170 dots   170 dots   0 dots    170 dots x 4 + 0 dots x 2        70 dots x 4

   280   18 mm       18 mm x 2     18.01 mm   17.92 mm   0.04 mm   18.01 mm x 2 + 0.04 mm x 2       18.01 mm x 2
                     0.70” x 2     256 dots   254 dots   1 dots    254 dots x 2 + 1 dots x 2        254 dots x 2

   286   18 mm       18 mm x 3     18.01 mm   17.92 mm   0.04 mm   18.01 mm x 3 + 0.04 mm x 2       18.01 mm x 3
                     0.70” x 3     256 dots   254 dots   1 dots    254 dots x 3 + 1 dots x 2        254 dots x 3

   292   18 mm       18 mm x 4     18.01 mm   17.92 mm   0.04 mm   18.01 mm x 4 + 0.04 mm x 2       18.01 mm x 4
                     0.70” x 4     256 dots   254 dots   1 dots    254 dots x 4 + 1 dots x 2        254 dots x 4

   281   24 mm       24 mm x 2     24.00 mm   23.99 mm   0.01 mm   24.00 mm x 2 + 0.01 mm x 2       24.00 mm x 2
                     0.94” x 2     340 dots   340 dots   0 dots    340 dots x 2 + 0 dots x 2        340 dots x 2

   287   24 mm       24 mm x 3     24.00 mm   23.99 mm   0.01 mm   24.00 mm x 3 + 0.01 mm x 2       24.00 mm x 3
                     0.94” x 3     340 dots   340 dots   0 dots    340 dots x 3 + 0 dots x 2        340 dots x 3

   293   24 mm       24 mm x 4     24.00 mm   23.99 mm   0.01 mm   24.00 mm x 4 + 0.01 mm x 2       24.00 mm x 4
                     0.94” x 4     340 dots   340 dots   0 dots    340 dots x 4 + 0 dots x 2        340 dots x 4




                                                - 15 -
                                                                                                   2. Print Data
                                                                                  Raster Command Reference




ID    Tape    Designation      1          3          5                     7                       8
      Size                                                   [3] x Split number + [5] x 2     [3] x Split
                                                                                               number

282   36 mm   36 mm x 2     36.09 mm   32.03 mm   2.03 mm   32.03 mm x 2 + 2.03 mm x 2       32.03 mm x 2
              1.4” x 2      512 dots   454 dots   29 dots   454 dots x 2 + 29 dots x 2       454 dots x 2

288   36 mm   36 mm x 3     36.09 mm   32.03 mm   2.03 mm   32.03 mm x 3 + 2.03 mm x 2       32.03 mm x 3
              1.4” x 3      512 dots   454 dots   29 dots   454 dots x 3 + 29 dots x 2       454 dots x 3

294   36 mm   36 mm x 4     36.09 mm   32.03 mm   2.03 mm   32.03 mm x 4 + 2.03 mm x 2       32.03 mm x 4
              1.4” x 4      512 dots   454 dots   29 dots   454 dots x 4 + 29 dots x 2       454 dots x 4




                                        - 16 -
                                                                                            2. Print Data
                                                                                    Raster Command Reference




2.3.3 Feed amount

     The feed amount (left and right margins) is defined below.
     360dpi x 360dpi
                                                                          Minimum margin
                                                                           setting with no
                                Minimum margin          Maximum margin
                Type                                                            precut
                                    setting                 setting
                                                                            （Unrelated to
                                                                               driver）

                              1 mm                    127 mm             27 mm
       Normal                 0.04"                   5.00"              1.06”
                              14 dots                 1800 dots          382 dots


     360dpi x 720dpi
                                                                          Minimum margin
                                                                           setting with no
                                Minimum margin          Maximum margin
                Type                                                            precut
                                    setting                 setting
                                                                            （Unrelated to
                                                                               driver）

                              1 mm                    127 mm             27 mm
       High resolution        0.04"                   5.00"              1.06”
                              28 dots                 3600 dots          764 dots




                                                  - 17 -
                                                                                             2. Print Data
                                                                                           Raster Command Reference




2.3.4 Maximum and minimum lengths

     The maximum and minimum lengths are defined below.
     TZe tape
     360dpi x 360dpi
                     Type                           Minimum length                   Maximum length

                                          4 mm                                 1000 mm
       Normal                             0.16”                                39.37”
                                          57 dots                              14173 dots


     360dpi x 720dpi
                     Type                           Minimum length                   Maximum length

                                          4 mm                                 1000 mm
       High resolution                    0.16”                                39.37”
                                          114 dots                             28346 dots


     Heat-Shrink Tube (not supported for PT-P910BT)
                     Type                           Minimum length                   Maximum length

                                          4.2 mm                               500 mm
       Normal                             0.16”                                19.69”
                                          60 dots                              7087 dots
     * The minimum length with the driver is based on the machine specifications (due to the machine cutter
     position), and the minimum length of tape that can be fed out is 27 mm.
     For example, even when the minimum print data of 4.2 mm is created, the print result will be the 27 mm
     of tape shown below, since the minimum length of tape that can be fed out is 27 mm.




     In other words, the print data will be on 27 mm of tape when the print data length is 27 mm or less.




                                                     - 18 -
                                                                                                    2. Print Data
                                                                                                                                                                    Raster Command Reference




2.3.5 Raster line

      As shown below, the parts with data to be printed are converted with “raster graphics transfer”, and the
      parts with no data are converted with “zero raster graphics”. On the actual tape, margins (feed) are
      added specified with “various mode settings” at the beginning and the end.

                        Feeding direction


                      Expansion direction                                                                                                              Print area



                                                                                             Rasterized




                                                                                                                              RasterLine 4
                                                                                                              Zero Raster 1
                                               RasterLine 1

                                                              RasterLine 2

                                                                              RasterLine 3

                                                                                              Zero Raster 1
                      Feeding direction


                                                                                                                                                       Print area



                                      Print head


      The following shows the relationship between the raster graphics parameters and the pixels.

                             MSB LSB        MSB LSB                               MSB LSB                                       MSB LSB
                                 st                 and                                                rd                                      th
                                1 B            2 B                                            3 B                                            4 B ...




                                                                             - 19 -
                                                                                                                                                                             2. Print Data
                                                                                                         Raster Command Reference




Total number of pins: 560pin

                           Number of pins
                           for right margin              Raster line
                                                                             Left and right margins
                                                         First byte




                              Number of
                              print area
                              pins




                     Total number                                     Print area
                     of pins




                                                         Last byte

                   0 pin   Number of pins
                           for left margin

                                                                Feeding direction
                                    Pins on print head




  TZe tape：
                                                                                   Number of pins
                              Number of pins        Number of print area                              Number of bytes for raster
         Tape Type                                                                   for right
                              for left margin             pins                                           graphics transfer
                                                                                      margin

          3.5 mm                     248                      48                        264                      70

           6 mm                      240                      64                        256                      70

           9 mm                      219                     106                        235                      70

           12 mm                     197                     150                        213                      70

           18 mm                     155                     234                        171                      70

           24 mm                     112                     320                        128                      70

           36 mm                      45                     454                        61                       70




                                                         - 20 -
                                                                                                                  2. Print Data
                                                                                   Raster Command Reference




Heat-Shrink Tube：
                    Number of pins    Number of print area   Number of pins     Number of bytes for raster
       Tape Type
                    for left margin         pins             for right margin      graphics transfer

      HS 5.8 mm          244                  56                   260                     70

      HS 8.8 mm          224                  96                   240                     70

      HS 11.7 mm         206                  132                  222                     70

      HS 17.7 mm         166                  212                  182                     70

      HS 23.6 mm         144                  256                  160                     70

      HS 5.2 mm          252                  40                   268                     70

      HS 9.0 mm          228                  88                   244                     70

      HS 11.2 mm         222                  100                  238                     70

      HS 21.0 mm         152                  240                  168                     70

      HS 31.0 mm          92                  360                  108                     70




                                          - 21 -
                                                                                            2. Print Data
                                                                       Raster Command Reference




1. Print Command List
    ASCII Code      Binary Code         Description

    NULL            00                  Invalidate

    ESC    @        1B   40             Initialize

    ESC    iS       1B   69   53        Status information request

    ESC    i    a   1B   69   61        Switch dynamic command mode

    ESC    i    z   1B   69   7A        Print information command

    ESC    i    M   1B   69   4D        Various mode settings

    ESC    i    A   1B   69   41        Specify the page number in “cut each * labels”

    ESC    i    K   1B   69   4B        Advanced mode settings

    ESC    i    d   1B   69   64        Specify margin amount (feed amount)

    M               4D                  Select compression mode

    G               67                  Raster graphics transfer

    Z               5A                  Zero raster graphics

    FF              0C                  Print command

    Control-Z       1A                  Print command with feeding

    ESC    i    !   1B   69   21        Switch automatic status notification mode




                                   - 22 -
                                                                     3. Print Command List
                                                                                            Raster Command Reference




1. Printing Command Details
NULL            Invalidate

       ASCII:            NULL
       Hexadecimal: 00

Description
⚫ Skipped
⚫ If data transmission is to be stopped midway, send the “initialize” command after sending the “invalidate”
    command for the appropriate number of bytes to return to the receiving state, where the print buffer is
    cleared.




ESC @           Initialize

       ASCII:            ESC    @
       Hexadecimal: 1B          40

Description
⚫ Initializes mode settings.
⚫ Also used to cancel printing.




ESC i S         Status information request

       ASCII:            ESC    i    S
       Hexadecimal: 1B          69   53

Description
⚫ Send a request to the printer for status information. For details on the status, refer to the previous section.
⚫ The size is fixed at 32 bytes.
   Note
   Before sending print data to the printer, this command should be sent once. Since error information
   is automatically sent by the printer during printing, do not send this command while printing.
   For details on transmission of the status, refer to “5. Flow Charts”.




                                                     - 23 -
                                                                                   4. Printing Command Details
                                                                            Raster Command Reference




Number   Offset   Size                   Name                         Value/Reference

  1        0       1     Print head mark                     Fixed at 80h

  2        1       1     Size                                Fixed at 20h

  3        2       1     Brother code                        Fixed at “B” (42h)

  4        3       1     Series code                         Fixed at “0” (30h)

                                                             PT-P900: Fixed at “q” (71h)
                                                             PT-P900W: Fixed at “o” (69h)
  5        4       1     Model code
                                                             PT-P950NW: Fixed at “p” (70h)
                                                             PT-P910BT: Fixed at “x” (78h)

  6        5       1     Country code                        Fixed at “0” (30h)

  7        6       1     Battery Level                       Refer to table (10) below.

  8        7       1     Extended error                      Refer to table (11) below.

  9        8       1     Error information 1                 Refer to table (1) below.

  10       9       1     Error information 2                 Refer to table (2) below.

  11      10       1     Media width                         Refer to table (3) below.

  12      11       1     Media type                          Refer to table (4) below.

  13      12       1     Number of colors                    Fixed at 00h

  14      13       1     Fonts                               Fixed at 00h

  15      14       1     Japanese fonts                      Fixed at 00h

                                                             Value specified where the “various
  16      15       1     Mode                                mode settings” command
                                                             00h if not specified

  17      16       1     Density                             Fixed at 00h

  18      17       1     Media length                        Refer to table (3) below.

  19      18       1     Status type                         Refer to table (5) below.

  20      19       1     Phase type

  21      20       1     Phase number (higher order bytes)   Refer to table (6) below.

  22      21       1     Phase number (lower order bytes)

  23      22       1     Notification number                 Refer to table (7) below.

  24      23       1     Expansion area (number of bytes)    Fixed at 00h

  25      24       1     Tape color information              Refer to table (8) below.

  26      25       1     Text color information              Refer to table (9) below.

  27      26       1     Reserved                            Fixed at 00h

31~32    30~31     1     Reserved                            Fixed at 00h




                                         - 24 -
                                                                  4. Printing Command Details
                                                                               Raster Command Reference




(1) Error information 1
                                                              PT-P900
                                                             PT-P900W                 PT-P910BT
     Flag     Mask                 Definition               PT-P950NW                （○：Supported,
                                                          （○：Supported,             -:Not supported）
                                                         -:Not supported）

      Bit 0   01h     “No media” error                       ○                           ○

      Bit 1   02h     “End of media” error                   ○                            -

      Bit 2   04h     Cutter jam                             ○                           ○

      Bit 3   08h     Weak batteries                         ○                           ○

      Bit 4   10h     Printer in use                         -                            -

      Bit 5   20h         (Not used)                         ○                           ○

      Bit 6   40h     High-voltage adapter                   ○                            -

      Bit 7   80h         (Not used)                         ○                           ○


(2) Error information 2
                                                              PT-P900
                                                             PT-P900W                 PT-P910BT
     Flag     Mask                 Definition               PT-P950NW                （○：Supported,
                                                          （○：Supported,          -:Not supported）
                                                         -:Not supported）

                      “Replace media” error                  ○                           ○
      Bit 0   01h     (with a serial connecting)
                      Wrong media

      Bit 1   02h     “Expansion buffer full” error          ○                            -

      Bit 2   04h     Communication error                    ○                           ○

                      “Communication buffer full”            ○                           ○
      Bit 3   08h
                      error

      Bit 4   10h     “Cover open” error                     ○                            -

      Bit 5   20h     Overheating error                      ○                           ○

                      “Black marking not detected”           ○                            -
      Bit 6   40h
                      error

      Bit 7   80h     System error                           ○                           ○




                                                - 25 -
                                                                       4. Printing Command Details
                                                                                     Raster Command Reference




(3) Media width and length
  The media width and length is described in millimeters. 0～255 (0 to FFh)
  (a) TZe tape
* Media Width: The tape width is indicated in millimeters.
* Media Length: Fixed at 00h
                                                                     PT-P900
                                                                    PT-P900W            PT-P910BT
          Media             Media Width     Media Length           PT-P950NW            （○：Supported,
                                                                 （○：Supported,      -:Not supported）
                                                             -:Not supported）

          No tape               00h               00h              ○                       ○

          3.5 mm                04h               00h              ○                       ○

           6 mm                 06h               00h              ○                       ○

           9 mm                 09h               00h              ○                       ○

          12 mm                 0Ch               00h              ○                       ○

          18 mm                 12h               00h              ○                       ○

          24 mm                 18h               00h              ○                       ○

          36 mm                 24h               00h              ○                       ○

        HS 5.8 mm               06h               00h              ○                        -

        HS 8.8 mm               09h               00h              ○                        -

       HS 11.7 mm               0Ch               00h              ○                        -

       HS 17.7 mm               12h               00h              ○                        -

       HS 23.6 mm               18h               00h              ○                        -

   FLe 21 mm x 45 mm            15h               2Dh              ○                        -




                                                - 26 -
                                                                             4. Printing Command Details
                                                                                          Raster Command Reference




(4) Media type
                                                             PT-P900
                                                            PT-P900W            PT-P910BT
          Media Type                 Value                 PT-P950NW            （○：Supported,
                                                         （○：Supported,      -:Not supported）
                                                     -:Not supported）

     No media                         00h                    ○                    ○

     Laminated tape                   01h                    ○                    ○

     Non-laminated tape               03h                    ○                    ○

     Fabric Tape                      04h                    ○                    ○

     Heat-Shrink Tube                                        ○                     -
                                      11h
     (HS 2:1)

     File tape                         13h                    ○                     -

     Flexible ID tape                 14h                    ○                    ○

     Satin tape                       15h                    ○                    ○

     Heat-Shrink Tube                                        ○                     -
                                      17h
     (HS 3:1)

     Incompatible tape                FFh                    ○                    ○


(5) Status type
                Status Type                          Value

     Reply to status request                          00h

     Printing completed                               01h

     Error occurred                                   02h

     Exit IF mode                               03h (not used)

     Turned off                                       04h

     Notification                                     05h

     Phase change                                     06h

     (Not used)                                   07h to 20h

     (Reserved)                                   21h to FFh
  If an error occurred during printing, the printer returns the error status.




                                                  - 27 -
                                                                                 4. Printing Command Details
                                                                                        Raster Command Reference




(6) Phase type and phase number
  If the phase number is not used, both are fixed at 00h.
                          Phase State                                       Phase Type

              Editing state (reception possible)                                  00h

                          Printing state                                          01h


  Editing state
              Phase                        Value (Dec.)      Higher Order Bytes         Lower Order Bytes

     Editing state (reception
                                                0                   00h                           00h
            possible)

              Feed                              1                   00h                           01h


  Printing state
              Phase                        Value (Dec.)      Higher Order Bytes         Lower Order Bytes

             Printing                           0                   00h                           00h

            (Not used)                         10                   00h                           0Ah

        Cover open while
                                               20                   00h                           14h
           receiving

            (Not used)                         25                   00h                           19h


(7) Notification number
                         Notification                                        Value

                        Not available                                         00h

                         Cover open                                           01h

                        Cover closed                                          02h

                     Cooling (started)                                        03h

                     Cooling (finished)                                       04h




                                                    - 28 -
                                                                           4. Printing Command Details
                                                                    Raster Command Reference




(8) Tape color information
            Tape color          Tape color ID         Notes

               White                01h

               Other                02h
               Clear                03h
                Red                 04h
                Blue                05h
               Yellow               06h
               Green                07h
               Black                08h
         Clear（White text）          09h
            Matte White             20h
            Matte Clear             21h
            Matte Silver            22h
             Satin Gold             23h
            Satin Silver            24h
                                                TZe-535(12 mm)
              Blue（D）               30h         TZe-545(18 mm)
                                                TZe-555(24 mm)
              Red（D）                31h         TZe-435(12 mm)
        Fluorescent Orange          40h
         Fluorescent Yellow         41h
           Berry Pink（S）            50h         TZe-MQP35
           Light Gray（S）            51h         TZe-MQL35
          Lime Green（S）             52h         TZe-MQG35
             Yellow（F）              60h
              Pink（F）               61h
              Blue（F）               62h
      White（Heat-shrink Tube）       70h
          White（Flex. ID）           90h
          Yellow（Flex. ID）          91h
             Cleaning               F0h
               Stencil              F1h
            Incompatible            FFh




                                     - 29 -
                                                            4. Printing Command Details
                                                                                  Raster Command Reference




 (9) Text color information
                          Text color                                    Text color ID

                             White                                          01h

                              Red                                           04h

                              Blue                                          05h

                             Black                                          08h

                              Gold                                          0Ah

                            Blue（F）                                         62h

                           Cleaning                                         F0h

                            Stencil                                         F1h

                             Other                                          02h

                         Incompatible                                       FFh


(10) Battery Level
     PT-P900/P900W/P950NW
                  Battery Level                                 Value
           Full                                                 00 h
           Half                                                 01 h
           Low                                                  02 h
           Need to be Charged                                   03 h
           Using AC adapter                                     04 h
           Unknown                                              FF h


     PT-P910BT
                  AC Adapter                Battery Level                Value
           AC Adapter                           Full                     20 h
           not connected                        Half                     22 h
                                                Low                      23 h
                                        Need to be Charged               24 h
           AC Adapter                           Full                     30 h
           connected                            Half                     32 h
                                                Low                      33 h
                                        Need to be Charged               34 h
                                        Battery not installed            37 h




                                                - 30 -
                                                                        4. Printing Command Details
                                                                         Raster Command Reference




(11) Extended error
                                                             PT-P900
                                                            PT-P900W          PT-P910BT
                 Error Type                 Value          PT-P950NW          （○：Supported,
                                                         （○：Supported,    -:Not supported）
                                                     -:Not supported）

                File tape end                 10h           ○                      -

     High-resolution/draft printing error    1Dh           ○                      -

          Adapter pull/insert error          1Eh           ○                      -

         Incompatible media error            21h           ○                     ○




                                            - 31 -
                                                                 4. Printing Command Details
                                                                                        Raster Command Reference




ESC i a        Switch dynamic command mode

      ASCII:           ESC      i     a     {n1}
      Hexadecimal: 1B           69    61    {n1}

Parameters
      Definitions of {n}:
      PT-P900/P900W/P950NW
          0: ESC/P mode (default)
          1: Raster mode (Be sure to switch to this mode.)
          3: P-touch Template mode
      PT-P910BT
          1: Raster mode (default)

Description
⚫ Dynamically switches between the printer's command modes. A printer that receives this command
    operates in the specified command mode until the printer is turned off.
⚫ The printer must be switched to raster mode before raster data is sent to it. Therefore, send this command
    to switch the printer to raster mode.




                                                     - 32 -
                                                                               4. Printing Command Details
                                                                                                    Raster Command Reference




ESC i z           Print information command

      ASCII:             ESC    i       z    {n1}    {n2}     {n3} {n4} {n5}      {n6}   {n7}    {n8}   {n9}    {n10}
      Hexadecimal: 1B           69      7A   {n1}    {n2}     {n3} {n4} {n5}      {n6}   {n7}    {n8}   {n9}    {n10}

Description
⚫ Specifies the print information.
⚫ Definitions of {n1} through {n10}

          {n1}:         Valid flag: Specifies which values are valid
                        #define PI_KIND 0x02                // Media type
                        #define PI_WIDTH 0x04               // Media width
                        #define PI_LENGTH 0x08              // Media length
                        #define PI_QUALITY 0x40             // Priority given to print quality (Not used)
                        #define PI_RECOVER 0x80             // Printer recovery always on


                        If flag 0x80 is specified…
                        ⚫ PT-P9100/900W/950NW:
                            Both “Printer recovery” and “bi-directional communication” will be activated.
                            The printer will send status notification when printing.
                        ⚫ PT-P910BT:
                            “bi-directional communication” will not be activated.
                            Please use “Switch automatic status notification mode” command to enable
                            bi-directional communication with the printer when printing.

          {n2}:         Media type
                        Laminated/Non-laminated tape: 00h
                        Heat-Shrink Tube (HS 2:1): 11h
                        Heat-Shrink Tube (HS 3:1): 17h
                        File tape: 13h
                        Incompatible tape: FFh


                        Note:
                        ⚫ PT-P9100/900W/950NW:
                            High-resolution printing and draft printing are supported for Laminated tape only.
                            Please set to 09h when printing.
                        ⚫ PT-P910BT:
                            High-resolution printing and draft printing are not supported.

          {n3}:         {n3}: Media width (mm)
                        {n4}: Media length (mm)
          {n4}:
                        For the media of width 24 mm, specify as n3 = 18h and n4 = 00h.



                                                        - 33 -
                                                                                          4. Printing Command Details
                                                                                 Raster Command Reference




           n4 is normally 00h, regardless of the paper length.

{n5-n8}:   Raster number = n8*256*256*256 + n7*256*256 + n6*256 + n5
           If the media is not correctly loaded into the printer when the valid flag for PI_KIND,
           PI_WIDTH and PI_LENGTH are set to “ON”, an error status is returned (Bit 0 of “(2) Error
           information 2” is set to “ON”.)

{n9}:      Starting page: 0
           Other pages: 1
           Last page: 2
           The output will be 2 regardless of starting/last page for the job consists of single page.

{n10}:     Fixed at 0




                                             - 34 -
                                                                        4. Printing Command Details
                                                                                 Raster Command Reference




ESC i M       Various mode settings

     ASCII:           ESC      i    M      {n1}
     Hexadecimal: 1B           69   4D     {n1}

Parameters
     Definitions of {n1}
     The meaning of each bit in a 1-byte parameter is described below.
     Bit 0 (Masked Bit = 0x01): (reserved)
     Bit 1 (Masked Bit = 0x02): (reserved)
     Bit 2 (Masked Bit = 0x04): (not used)
     Bit 3 (Masked Bit = 0x08): (not used)
     Bit 4 (Masked Bit = 0x10): (not used)
     Bit 5 (Masked Bit = 0x20): (not used)
     Bit 6 (Masked Bit = 0x40): Auto cut
     Bit 7 (Masked Bit = 0x80): Mirror printing


     ⚫    Auto cut
          1: Automatically cuts
          0: Does not automatically cut
     ⚫    Mirror printing
          1: Mirror printing
          0: No mirror printing




                                                  - 35 -
                                                                         4. Printing Command Details
                                                                                                 Raster Command Reference




ESC i K       Advanced mode settings

     ASCII:              ESC     i      K    {n1}
     Hexadecimal: 1B             69     4B   {n1}

Parameters
  Definitions of {n1}
  The meaning of each bit in a 1-byte parameter is described below.
  0bit: Draft printing
          1: Draft printing
          0: Normal printing
          For PT-P910BT, please set this value as 0 (Draft printing is not supported).
  1bit: Not used
  2bit：Half cut
          1: Half cut on
          0: Half cut off
  3bit：No chain printing
          When printing multiple copies, the labels are fed after the last one is printed.
          1: No chain printing（Feeding and cutting are performed after the last one is printed.）
          0: Chain printing（Feeding and cutting are not performed after the last one is printed.）
  4bit：Special tape (no cutting)
          Labels are not cut when special tape is installed.
          1: Special tape (no cutting) ON
          0: Special tape (no cutting) OFF
  5bit: Not used
  6bit：High-resolution printing
          1: High-resolution printing
          0: Normal printing
          For PT-P910BT, please set this value as 0 (High-resolution printing is not supported).
  7bit：No buffer clearing when printing (Not used for PT-P910BT)
          The expansion buffer of the machine is not cleared with the “no buffer clearing when printing”
          command.
          If this command is sent when the data of the first label is printed (it is specified between the “initialize”
          command and the print data), printing is possible only if a print command is sent with the second or
          later label.
          1:No buffer clearing when printing ON
          0:No buffer clearing when printing OFF




                                                       - 36 -
                                                                                       4. Printing Command Details
                                                                                         Raster Command Reference




ESC i d        Specify margin amount (feed amount)

      ASCII:           ESC         i    d       {n1}   {n2}
      Hexadecimal: 1B              69   64      {n1}   {n2}

Description
⚫ Specifies the amount of the margins.
⚫ Margin amount (dots)=n1+n2*256
    (a) Continuous length tape
                              Paper          Tape       Print area




                                        Margin amount             Cut line




ESC i A        Specify the page number in “cut each * labels”

      ASCII:           ESC     i        A      {n}
      Hexadecimal: 1B          69       41     {n}

Parameters
      Definitions of {n}
      Page number = n1 (1 - 255)
      Default is 1 (cut each label).
      If 00h is set, label will not be cut.

Description
⚫   When “auto cut” is specified, you can specify page number (1 - 255) in “cut each * labels”.




                                                         - 37 -
                                                                                4. Printing Command Details
                                                                                              Raster Command Reference




M               Select compression mode

       ASCII:           M        {n}
       Hexadecimal: 4D           {n}

Parameters
       Definitions of {n}
        0       No-compression mode (Enabled)
        1       Reserved (Disabled)
        2       TIFF (Enabled)

Description
⚫ Selects the compression mode. Data compression is available only for data in raster graphic transfer.

[TIFF(Pack Bits)]
⚫ 1-byte units
⚫ If the same data is repeated, the number of data units and that 1 byte of data are specified.
    If different data is in a series, the number of data items and all of the different data are specified.
⚫ If the same data is repeated, the number of data units is specified as the actual number minus 1, expressed
    as a negative number.
    If different data is in a series, the number of data units is specified as the number of bytes minus 1,
    expressed as a positive number.
⚫ If the above process results in more than 70 bytes of compressed data, the data is treated as being all
    different. As a result, the data will be 71 bytes, including the 1 byte that specifies the data length.

Example
1 raster of raster graphics transfer:
       Without compression:        00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
                                   00 00 00 00 00 22 22 23 BA BF A2 22 2B……

       With compression:           ED 00 FF 22 05 23 BA BF A2 22 2B …
                                    a      b        c


       a.     Since “00h” is repeated for 20 bytes, 20d -> 19d -> 13h changed into a negative number is EDh.
              Therefore: ED 00
       b.     Since “22h” is repeated for 2 bytes, 2d -> 1d -> 1h changed into a negative number is FFh.
              Therefore: FF 22
       c.     The following 6 bytes remain unchanged. 6d -> 5d -> 5h
              Therefore: 05 23 BA BF A2 22 2B
       Continue for the remaining number of bytes for the uncompressed data. Even if 00h continues until the
       end, it cannot be omitted.




                                                      - 38 -
                                                                                     4. Printing Command Details
                                                                                                              Raster Command Reference




Explanation of “TIFF compression mode”
With compression, the data for the “raster graphics transfer” command is based on 70 bytes of the total number
of pins (560). As shown below, with no compression, the sum of the number of offset pins and the number of
pins within the print area is the byte data. However, with compression, the number of unused pins is also added
to the data. In other words, with compression, this becomes 70 bytes when it is expanded by the printer,
regardless of the tape width.

                                                      Raster line with      Raster line with
                                                      compression           no compression

                                              0 pin
                                                                           First byte


                                  Number
                                  of offset                                                  Tape margin
                                  pins




                                Number of
                                print area
                                pins

                       Total
                       number
                       of pins

                                                                                Print area




                                Number
                                of unused
                                pins                                              Feeding direction

                                                               Last byte

                                      Pins on print head




                                                              - 39 -
                                                                                                      4. Printing Command Details
                                                                                         Raster Command Reference




G               Raster graphics transfer

       ASCII:           G          {n1} {n2} {d1}   ...     {dk}
       Hexadecimal: 47             {n1} {n2} {d1}   ...     {dk}

Description
⚫ Transfers the specified number of bytes (k) of data.
⚫ The data is expanded by overwriting from the position where the margin was added.
⚫ If the expanded data does not reach the end of the expansion buffer, the remainder is filled with 0 data.
⚫ If the expanded data exceeds the end of the expansion buffer, the excess is cut off.

Parameters
       {n1}{n2} Specified number of bytes k = n1 + n2*256
                     0000h ≦ Specified number of bytes k ≦ First positive number that exceeds the value
              of the number of print head pins divided by 8 (Gauss number)
       {k} Number of bytes of raster data (d1 to dk)
              However, use the following value if no compression is specified as the compression mode.
              k=70
       {d1~dk} Raster data.




Z               Zero raster graphics

       ASCII:           Z
       Hexadecimal: 5A

Description
⚫ Fills raster line with 0 data.




FF              Print command

       ASCII:           FF
       Hexadecimal: 0C

Description
⚫ Used as a print command at the end of pages other than the last page when multiple pages are printed.




                                                          - 40 -
                                                                                4. Printing Command Details
                                                                                       Raster Command Reference




Control-Z       Print command with feeding

      ASCII:             Control-Z
      Hexadecimal: 1A

Description
⚫ Used as a print command at the end of the last page.




ESC i !         Specify automatic status notification mode

      ASCII:             ESC     i    !    {n1}
      Hexadecimal: 1B            69   21   {n1}

Parameters
   Definitions of {n1}
   0: Notify.
   1: Do not notify. (default)

Description
⚫ Dynamically switches whether the automatic status notification is given during printing. A printer that
    receives this command operates in the specified command mode until the printer is turned off.
⚫ Use this command when building a system where the status is not obtained.




                                                  - 41 -
                                                                               4. Printing Command Details
                                                                                         Raster Command Reference




1. Flow Charts


Normally, printing is performed as buffered printing.
However, if the printer is connected via USB and uncompressed data is received, concurrent printing is
performed.


Note:
Concurrent printing：Printing starts immediately after the printer receives print data.
Buffered printing：Printing starts after one page of print data is received.




                                                        - 42 -
                                                                                               5. Flow Charts
                                                                                                  Raster Command Reference




5.1 Concurrent printing normal flow for USB connection


                     Computer (host)                                                         Printer
                                                           Invalidate                              The printer is
                                                                                                   reset.
  If there are no                                             Initialize                          The printer is
  problems with the
                                                                                                  initialized.
  printer status (media,
  etc.), the data is    READ                 Status information request                           The status of the
  transmitted. If there                                                                           printer (media, etc.)
  is a problem, an error                                                                          is checked and a
  appears.                              Status (response to status information request)           response is sent.

      Displaying sending                                                                         Data received.
                                               Sending control codes
                                                                                                       Beginning printing
                                                                                                       without waiting for
                                                Sending raster data                                    a print command

                                                                                Status
                                                                           (Phase change:          Printing
                                                                              “Printing”)


                                                Sending raster data

                                                Sending raster data

                                                Sending raster data



         Display ing printing     Sending a print command (print command with feeding (1A)
                                  for the last page or print command (0C) for other pages)
                         READ
  Phase change
  “Printing” received.
  “Printing completed”                         Status (“Printing completed”)                           Printing of the 1st
  received.                                                                                            page is actually not
                                                                                                       finished, but the
                                               Status (Phase change:                                   “Printing
                                                “Waiting to receive”)                                  completed” status
  Finishing process for
                                                                                                       and “Waiting to
  printing page 1                                                                                      receive” phase are
                                                                                                       sent.
  Sending data for page 2
                                             Sending control code/raster data


                                                                                Status             Printing 1st page
                                                                           (Phase change:
                                                                              “Printing”)          Printing 2nd page


                                                Sending raster data

                                                Sending raster data


                                                Sending raster data




                                                        - 43 -
                                                                                                           5. Flow Charts
                                                                                                    Raster Command Reference




5.2 Concurrent printing error flow for USB connection (when feeding at the end of the page)

                    Computer (host)                                                             Printer
                                                        Invalidate                                   The printer is
                                                                                                     reset.
                                                         Initialize                                  The printer is
If there are no
problems with the                                                                                    initialized.
printer status (media,                  Status information request
etc.), the data is       READ                                                                        The status of the
transmitted. If there is                                                                             printer (media, etc.)
a problem, an error                                                                                  is checked and a
                                        Status (response to status information request)
appears.                                                                                             response is sent.

     Displaying sending                     Sending control codes                                    Data received.

                                                                                                     Beginning printing
                                             Sending raster data                                     without waiting for a
                                                                                                     print command
                                                                                Status
                                                                           (Phase change:            Printing
                                                                              “Printing”)


                                             Sending raster data


         Displaying printing    Sending a print command (print command with feeding (1A)
                                for the last page or print command (0C) for other page)
                       READ
     Phase change
    “Printing” received.
                                                                                                     Printing of the 1st
     “Printing completed”                Status (“Printing completed”)                               page is actually not
    received.                                                                                        finished, but the
                                                                                                     “Printing completed”
    Finishing process                     Status (Phase change: “Waiting to receive”)                status and “Waiting
    for printing page 1                                                                              to receive” phase are
                                                                                                     sent.
    Sending data for page 2
                                        Sending control code/raster data

                                                                                                          Error occurred
                                                                                 Status
                                                                           (“Error occurred”)

                                             Sending raster data
                                                                                                    If an error occurs, all
                                                                                                    data read from the
         Displaying printing
                                             Sending raster data                                    computer is cleared.


         Displaying printing    Sending a print command (print command with feeding (1A)
                                for the last page or print command (0C) for other pages)
                      READ
 “Error Occurred” received.
An error appears.
When restarted, data is
resent starting with the
1st page since “Printing”
for the 2nd page is not
received.

    Resending process                                                                                Reprinting 1st page
    for data of 1st page                                 Initialize




                                                      - 44 -
                                                                                                            5. Flow Charts
                                                                                                          Raster Command Reference




5.3 Concurrent printing error flow for USB connection (with a concurrent printing error such as end
     of tape)

                           Computer (host)                                                        Printer
                                                                                                        Any jobs with errors
                                                                    Invalidate                          remaining in the printer
If there are no                                                                                         are cleared.
                                                                    Initialize                           The printer is initialized.
problems with the
printer status (media,
etc.), the data is                              Status information request                              The status of the printer
transmitted. If there is   READ                                                                         (media, etc.) is checked
a problem, an error                           Status (response to status information request)           and a response is sent.
appears.
            Displaying sending                    Sending control codes                                 Data received.

                                                   Sending raster data                                    Beginning printing
                                                                                                          without waiting for a
                                                                                                          print command
                                                                                    Status
                                                                               (Phase change :            Printing
                                                                                  “Printing”)

                                                   Sending raster data

            Displaying printing      Sending a print command (print command with feeding (1A)
                                     for the last page or print command (0C) for other pages)
                            READ
Phase change
“Printing” received.
                                                                                                          Printing of the 1st page
“Printing completed” received.                 Status (“Printing completed”)                              is actually not finished,
Phase change                                                                                              but the “Printing
“Waiting to receive” received.                 Status (Phase change: “Waiting to receive”)                completed” status and
                                                                                                          “Waiting to receive”
Finishing process for                                                                                     phase are sent.
printing page 1
Sending data for page 2                        Sending control code/raster data

                                                                                    Status                Printing 1st page
                                                                               (Phase change :
                                                                                                          Printing 2nd page
                                                                                  “Printing”)

                                                   Sending raster data

                                                                                   Status                     Error occurred
                                                                             (“Error Occurred”)
                                                                                                        If an error occurs, all
                                                   Sending raster data                                  data read from the
                                                                                                        computer is cleared.
          Displaying printing        Sending a print command (print command with feeding (1A)
                                     for the last page or print command (0C) for other pages)
                          READ
  Phase change
  “Printing” received.
   “Error Occurred” received.
 An error appears.
 When restarted, data is resent
 starting with the 2nd page
 since “Printing” for the 2nd
 page is received.

 Resending process for                                                                                  Reprinting 2nd page
 data of 2nd page                                                   Initialize




                                                           - 45 -
                                                                                                                 5. Flow Charts
                                                                                                     Raster Command Reference




5.4 Buffered printing normal flow for USB/Bluetooth connection

                        Computer (host)                                                           Printer

                                                              Invalidate                                The printer is
                                                                                                        reset.
 If there are no                                               Initialize                               The printer is
 problems with the                                                                                      initialized.
 printer status (media,                               Status information request                       The status of the
 etc.), the data is       READ                                                                         printer (media, etc.)
 transmitted. If there is                                                                              is checked and a
 a problem, an error                        Status (response to status information request)            response is sent.
 appears.

          Displaying sending                            Sending control codes                          Data received.


                                                         Sending raster data


                                                         Sending raster data

                                                         Sending raster data

                                                         Sending raster data


            Displaying printing       Sending a print command (print command with feeding (1A)
                                                                                                            Printing
                                        for the last page or print command (0C) for other page)


 Phase change              READ                                Status
 “Printing” received.                                 (Phase change: “Printing”)


 “Printing completed”                                            Status
 received.                                              (“Printing completed”)


 Phase change                                                 Status
 “Waiting to receive” received.                  (Phase change: “Waiting to receive”)
 Finishing process for
 printing 1st page                                                                                     Printing 1st page
 Sending data for                                                                                      Printing 2nd page
 2nd page
                                                        Sending control codes


                                                         Sending raster data



                                                         Sending raster data




                                                           - 46 -
                                                                                                              5. Flow Charts
                                                                                                 Raster Command Reference




5.5 Buffered printing error flow for USB/Bluetooth connection


                    Computer (host)                                                        Printer
                                                        Invalidate                               The printer is reset.

                                                        Initialize                               The printer is
                                                                                                 Initialized.
  If there are no
  problems with the                            Status information request                        The status of the
  printer status                                                                                 printer (media, etc.)
                         READ                                                                    is checked and a
  (media, etc.), the
  data is transmitted.                    Status (response to status information                 response is sent.
  If there is a problem,                     request) or an error is displayed
  an error appears.


       Displaying sending                        Sending control codes                           Data received.


                                                   Sending raster data

                                Sending a print command (print command with feeding (1A)         Printing
       Displaying printing      for the last page or print command (0C) for other page)

                       READ
    Phase change                                        Status
    “Printing” received.                       (Phase change: “Printing”)



                                                Status (“Error Occurred”)
                                                                                                     Error occurred




                                                     - 47 -
                                                                                                       5. Flow Charts
                                                                                         Raster Command Reference




5.6 Normal Flow for Network (Standard TCP/IP port) Connection

  *With a network connection, print data from the operating system’s port monitor is simply sent as is.
    When it prints 2 pages data

                         Computer                                                    Printer
                          (host)

 Divide print data                            Sending raster data
 into particular size,
 and send it.
                                              Sending raster data


                                              Sending raster data


                                              Sending raster data                              Receive data


                                              Sending raster data

                                                                                               As one page data
 End process for                              Sending raster data                              receives in the
 printing 1st                                                                                  printer buffer, start
                                                                                               printing
 Sending data for                             Sending raster data                              Printing 1st page
 2nd page
                                                                                               Printer buffer is
                                              Sending raster data                              full
                                BUSY


                                              Sending raster data
                                BUSY


                                              Sending raster data
                                BUSY


                                              Sending raster data
                                BUSY

                                              Sending raster data


                                              Sending raster data


                                              Sending raster data

                                                                                               As 2nd page data
                                              Sending raster data                              receives in the
                                                                                               printer buffer, start
                                                                                               printing.
 At host side, as sending                     Sending raster data
 print data has completed,                                                                     Printing 2nd page
 the print job data is
 erased.

 The print job is treated to
 be completion at printer
 side




                                                   - 48 -
                                                                                                 5. Flow Charts
                                                                                        Raster Command Reference




Appendix A: USB Specifications
  USB specifications 1.1
              Item                                             Description

           Vendor ID          0x04F9

                              PT-P900W 0x2085

           Product ID         PT-P950NW 0x2086
                              PT-P900 0x2083
                              PT-P910BT 0x20c7

              Class           Printer

       Character string for   Character string descriptor: 0x01
         manufacturer         0x0409: “Brother”

       Character string for   Character string descriptor: 0x03
         serial number        0x0409: “000” + Last nine digits of the printer’s serial number

         Device speed         Full speed

      Number of interfaces    1 (No alternate interfaces)

    With the printer class

          Power supply        Self-powered (As a printer class, Bus power is also set to “ON”.)

                              In bulk (Sends the status from the printer to the computer.)
           End point 1
                              Maximum packet size: 64 bytes

                              Out bulk (Sends print commands and data from the computer to the printer.)
           End point 2
                              Maximum packet size: 64 bytes




                                                 - 49 -
                                                                           Appendix A: USB Specifications
                                                                                     Raster Command Reference




Appendix B: Introducing the Brother Developer Center
Useful information for developers, such as applications, tools, SDKs as well as FAQs, are provided in the
Brother Developer Center.
http://www.brother.com/product/dev/index.htm




                                                 - 50 -
                                                    Appendix B: Introducing the Brother Developer Center
