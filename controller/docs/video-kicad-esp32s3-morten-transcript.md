# Transcript — "ESP32-S3 Simple TestBoard designed in KiCad"

Source: <https://www.youtube.com/watch?v=Z5AQMZh3qXw> — *made by morten*, uploaded
2026-08-21, 2:29:31. Audio pulled with `yt-dlp`, transcribed 2026-08-21 with
OpenAI Whisper `large-v3-turbo` (CUDA), then blocked into ~45-second paragraphs
with the timestamp of each block's first segment.

**Machine transcript — not proofread.** Whisper mangles part numbers and repeats
filler ("and and and", "by by by") during silent stretches where morten is
clicking rather than talking. Known misreadings: "KiCat" = KiCad, "room module"
= WROOM module, "LGO"/"LTO" = LDO, "quick" = Qwiic, "screw tunnel" = screw
terminal, "school" = screw, "spark phone" = SparkFun, "via/VR/VS/view/severe" =
via, "source free/smooth" = RGB colour names, "freedom model" = 3D model,
"gerber" is usually right. 1:21:25–1:22:30 and 2:21:25 are largely garbled —
the board is silent there.

The digested findings live in
[video-kicad-esp32s3-morten.md](video-kicad-esp32s3-morten.md); the decisions
they feed live in [../DESIGN.md](../DESIGN.md).

---

[0:00:00] Hi guys, I'm working on a small and very simple ESP32-S3 testboard in KiCat and it's based on the room module. This video will go through the whole process from making and designing the schematic to routing and ordering the PCB. The main features for this board are an ESP32-S3 room module with 8 megabytes of flash, a button for reset, user button, user RGB LED, an expansion header, programming header and a power LED on the 3 volt rail. For the mechanical size of things we will have four 3.2 millimeter mounting holes, the size will be 45 by 45 millimeters and it will be a four layer board design. And just before we start the project I would like to thank PCBWay for making this video

[0:00:51] possible. Remember that there are a large section on PCBWay.com where you can find a lot of projects and inspiration from other makers. If you find a particular project interesting then you can often directly order the PCB at PCBWay. You'll find my affiliate link in the video description of this video, please use it and thereby support the channel. So remember to visit PCBWay.com. So let's dig into it. So here we are in the KiCat project manager. I already created this project called ESP32-S3-Small and we have both here a schematic file and a PCB file. So let's get started doing the schematic design. Just double click here on the schematic file and here we have a blank canvas. So the first thing I normally

[0:01:42] do is to go into page settings to identify what I'm actually doing, which project I'm working on and let's fill in the date. We just click on these arrows here. Revision 1.0. The tile that's an ESP32-S3-Small testboard company. That's the YouTube channel name made by Morten and I think this is good for now. And then you see down here, this has been automatically filled in and we are ready to start the design.

[0:02:33] So we are going to use the ESP32-S3 room module. So let's get started placing some of the parts we need. So we go to place symbols and we will search for an ESP32-S3 and we have different models to choose from. And we are just loading some of the libraries. I have different models here. Let's see what we can find. Yeah, I think this one. This is one I made in a previous project.

[0:03:23] You can see the way the pins are organized here. It's a bit messy. And also for this one for another room module. So I re-routed some of the pins where they are placed in order to get a better overview. But you can of course download this project on my GitHub. And there is also the libraries that are being used in this project. So let's place the module here. And zoom in. So the first thing we would like to place is give some power and some decoupling capacitors to this module. So let's place power symbols. Let's press P.

[0:04:14] And we will use a 3.3 volt net. And for the crowd pins. Something like this. Something like this. And let's place some ground. And I would like the ground symbol to be a bit closer or the text for the ground to be a bit closer there.

[0:05:00] And we need some decoupling capacitors on the 3.3 volt net. Place symbols. And let's look for a capacitor. And I would like to use this small symbol. And normally I place a 10u. There. And of course a 100 nano. And we just press Ctrl D for duplicate.

[0:05:50] And then we edit the text here. 100 nano. And then we can just duplicate the ground symbol here. Mark it and press Ctrl D. There we should maybe have this a bit further out. Then we can take the wire along. Like that. So now we have C1 and C2.

[0:06:38] We have ground connected. Then we have the enable signal. And that's one of the signals that we are going to use from the programmer. And we would also like to have a button here. So we can actually reset the module. So the enable signal here is actually the reset pin as well. So let's place a wire here. And we would like to have a small button here. Where we can push and then reset the ESP32 S3. And we do that by connecting this pin to ground. And we would like to have a switch.

[0:07:24] And that should just be a single. Let's see. So symbol for push button. I think this is the one. And then we will connect that to ground. And we can remove this small stop here. Like that.

[0:08:12] But of course we need. To have a pull up pin. Or pull up resistor. And a capacitor here. In order to time the correct. Pulse for the reset. It needs to charge a capacitor. And that will be done through a 10 kilo ohm resistor. So let's find a resistor. And we can put that around here. We will take the 3.3 volt net. And just copy that. And we will need a capacitor as well.

[0:09:13] To make this RC filter. And that will be a 1 micro. And we will change this to a 10 kilo ohm resistor. I think that's it. And when we have this button here. And we will have our finger. Getting close to the enable signal. Then we will also protect it. By using a small ESD diode. Place symbol.

[0:10:00] And there will be an ESD. I have it already here. It will protect the 3.3 volt line. And we can just remove. Yeah. We will just keep the text as is. Like that. Maybe we should just move this down a tiny bit. And we can move this as one as well. I like there's a bit of symmetry in it.

[0:10:45] It's easier to read the schematic then. Like that. So now we have the most important things. For the ESP32 room module. There are some things we need to take care of. When we look at the pins. On the ESP32. There are some strapping pins. So I have this text already prepared. We can just go through it. Let's copy it. And then we can insert a small text box here. And paste the text in here.

[0:11:41] Something like this. And we can move it up a bit. Like that. So we have to be aware of some of the pins. If we use an ESP32 S3 with embedded RAM. So we need to take care of not using. IO35, IO36 and IO37. They are being used internally. So we can just check it over here. There is a small star here. That says okay. Please have a look on. On these pins. If you are. If you want to have a module with embedded RAM inside.

[0:12:32] But if you don't have a module with that. Then you are free to use these pins. And then you have to be aware of the strapping pins. That's GPIO 0 and 3. And then 45 and 46. So it's easier just to not play with these pins. If you have enough pins. If you are using all the pins. Then you should be aware of how these pins behave. So the only thing that we need to do. Is to put a pull up resistor on GPIO number 3. And normally we just put a 10 kilo resistor on that one. And GPIO 0 is used for the programming.

[0:13:21] Along with the ESP enable signal. And the RX and TX pins. That we are going to fill in on a connector. But a bit more on that later. So let's just connect a 10 kilo ohm resistor. To GPIO 3. I think we can do it like that. I think we can do it like that. Like that. Maybe one. And up there.

[0:14:06] So we need to program the ESP32 S3. And in this project. I would like to do that from a small pin header. And a programmer from ESP32 S3 called ESP32 PROC. And this is this one you can see here on the picture. There is a 6 pin connector. And a 10 pin connector. And there are also some smaller programming pins here. These are 1.27 millimeters. And this is the standard 2.54 millimeter pin headers. And I do this in this project. Because I want to avoid to put a USB to UART circuitry on.

[0:14:55] Along with some extra transistors and extra stuff. It's just in order to keep the board very simple. So I have this programmer lying around. And then I'll just connect this 6 pin connector to my ESP S3. Using these pins. And there is a board definition of that connector here. So this 6 pin connector. So we will just need to define this connector here in the schematic. And then we can program it from the ESP32 PROC. So we have enable, txd, rxd. And the power, vdd and ground. And then the ESPIO0. And ESPEnable, that's the reset pin.

[0:15:45] So let's put in our 6 pin connector. So place symbols. And we will need a connector. We can just say collapse all here. And remove this. And let's see. Let's see if we can find a generic one.

[0:16:36] There's a lot to choose from. Generic. And I need a one, two by three. And we need to place some pins here. And we need to place some pins here. On this side we have the enable signal.

[0:17:24] And we do that by saying place. And then we can place a net label. And that's an L. So if we just press L here on the keyboard. Then we can put in a label. And we will call that ESP underscore enable. And then we have it here. So here we have the txd line. And here we have the rxd line. Just like to have it a bit further out.

[0:18:15] Like this like this like that. And then we can have the same length over here. And there we have the 3.3 volt line. And here we have the ground. And we should move that a bit in there. Here you can press G. If you want to move this. Just move the cursor over here.

[0:19:01] Press G. Then you can move the line. And we will have the ground symbol down here. Duplicate. And ground. And let's grab a 3.3 volt net. And put that in here. And here we have the io0. L for label. ESP io0. Something like this.

[0:19:56] Then we have the programmer in place. And we have the enable. In order to connect this. Then we will duplicate the net here. And then just put it up here. Then we have the pin connected. And then we have io0. Just take everything here. And we will move it up here. Move it a bit further in here. G. Like that. I find it very useful to just duplicate the names.

[0:20:43] Instead of writing them. Then you are sure that you have exactly the same name. So of course we need to power this. This will not be connected to the USB port. So we will power this by a small screw tunnel. So let's find one of those. And we will just add the 5 volt to the board. And then regulate it down to 3.3 volt. Using a small LGO. So let's first place the screw tunnel. And it's a 2 pin.

[0:21:33] And let's move this around a bit. Transform selection. And mirror it horizontally. Like that. Like that. And then we can just call it school. Like that. Designator over there. And let's place an LGO. And normally I use the LM1117.

[0:22:26] 3.3 volts. And we can see here. There are different types. And normally I use. This one in a SUT223 housing 3 pin. So let's place that. Sorry. And we can wire the power. Like that.

[0:23:13] And we need a ground symbol here. Connect this one to ground. Let's grab a ground symbol down here. And then we need a ground symbol here. Save this. And then we need room for a decoupling capacitor. So let's try and place a capacitor.

[0:24:03] Let's make a bit more room for that. To the input capacitor. And we can grab the symbol over here. Just 10 micro here. Duplicates. And I think we need a bit more room. Still. Like that. And we can just copy this to the other side as well. And here we have our 3.3 volt net.

[0:25:06] Duplicate. Like that. And we have our 5 volt net. Plus 5 volts. Like that. So here we have the power. Coming in. And I would like to have an RGB LED as well. And I would like to have a dedicated power LED. So we can start with the dedicated power LED. That will be powered from 3.3 volt.

[0:25:53] It's easy like that. And then we need a current limiting resistor. And I think that 1k is fine. Place. Place. And LED. Let's just assemble LED. And we should make that a green LED. Like that.

[0:26:53] Then we have the RGB LED. Place. Symbols. And I have this symbol here. Already defined. And that's a common anode. Place it here. And we just need to. Give it 3.3 volts here on the anode. And then we have three lines here.

[0:27:40] For the RGB colors. And we can just put the pins on. Of course we need the current limiting resistors. First. Add. Let's see how this looks. I could maybe remove the value over here.

[0:28:45] Add. Duplicate. Check another thing here. And duplicate. Add. And let's call this. Label. LED. Was it blue? Red. Stand like that.

[0:29:33] And label. LED. Red. This is this one. And LED green. Like that. And then we can take these three labels. Duplicate them. And then move them over here. And then we can place them on. Some of the GPIO pins a bit later. And save. Then I would like to have a user button as well.

[0:30:23] A small button for my application. So we can just take this. And duplicate it. And just place it down here. Maybe. And we will just call that. User switch this. Wire here. And duplicate that label. Put it over here. And then we can assign that to a GPIO pin. Later. And I would like to have a.

[0:31:14] Quick. Connector as well. This is this four pin. Connector that can interface to different. Quick modules. So you can insert different. Or interface to different modules. That have this quick interface. And that's just a simple four pin connector. And then we'll assign the footprint for that. We will have to look at that a bit later. But that's just a four pin connector. And we will remove the filter here. And I have a connector here. One by four. And let's place it here.

[0:32:06] And transform it. I would like to have it mirrored vertically. Because pin number one is ground. On this quick connector. And duplicate it. Then we have the 3.3-4 line. That's on pin number two. Like that. And then we have SDA and SCL. And we need to have pull up resistors.

[0:32:51] On the I2C pins. So we can just grab it here. Have it on the same height. Maybe a bit longer out here. Then we have room for the labels. Like that. Maybe get this a bit closer over here. And then we have SEL.

[0:33:37] That's on pin number four. Label. SEL. And we have the SDA line. On pin number three. And press G. Something like that. In the color scheme for the connectors. We can just add a small text here. Draw text. So we have ground.

[0:34:27] That's on the black wire. And we have VCC. That's on a red wire. Then we have SDA. That's on a blue wire. And SCL. That's on a yellow wire. Like that. And we can align that. To the left side. Just a small information here.

[0:35:21] So here we have the. Quick connector. So what else do we need? We need some mounting holes. Four mounting holes. Just 3.2 millimeter mounting holes. And we can find that. Let's see here. Mounting. Mounting hole here. And we just need four of them. Duplicate. Like that.

[0:36:14] Yeah. And I would also like to break out some of the GPIOs. We have a lot of GPIOs here in the project. We haven't used that many. We can also take the SEL and SDA lines. And move that over here. So I will use a 10 pin connector. And then route six GPIOs over there. And also have some of the pins for 3.3 volts. And some from ground. Two for 3.3 volts. And then two for ground. So let's place a 10 pin connector. And we will find that in generic connectors.

[0:37:12] So that's 2 by 5. Odd even. And I think I will just call this. Sorry. I just wanted to rename this one. Pin. Two by three. And then we can also give this a name.

[0:38:09] Pin. Two by five. Like that. And now we add it. Let's grab some of the symbols here. Like that. And we can duplicate this.

[0:39:12] Like that. And then we need the ground. Like that. And then we need to assign some IOs. And I think we will just use. Like IO 10. To 15. Label.

[0:40:05] IO 10. IO 12. And IO 14. And here we will have IO 11. And IO 13. IO 15. So that's quite simple. So we can just.

[0:40:52] Mark those. And duplicate it. And now we have the. Labels ready over here. Now you see it's a bit messy here. So it would be nice to. Just align everything a bit. And make some boxes. And we can take the switch. Up here. Something like this. And maybe you can take. Circuitry here. And move it to the right.

[0:41:43] Like that. And let's divide it. In some smaller boxes. And we can do that by placing some. Or draw some lines. Like that. And we can move it a bit. Press in for move.

[0:42:29] Like this. And then we can. Duplicate that one. And place it. In the middle here. Approximately maybe we can move this. A bit further over. Like that. Like that.

[0:43:23] And then I would like. To have the RGB leds here. Our breakout connector. From here. We can move our. Mounting pins down here. And the power led. There. Quick connector. A bit further up. And our programming header. Around here. Around here. So it seems to be.

[0:44:35] Placed. So it gives a better overview. Of what we have. Maybe take. Grab this. And bring. Down a bit. Down a bit. That's fine. And let's divide. The smaller boxes. Place. Lines. A small mistake there. I made a small mistake there. And.

[0:45:25] Duplicate this. Duplicate. And duplicate. Something like this. And let's give the boxes. And let's give the boxes. A small label. A small label. And we can.

[0:46:10] Place. Text. And we will call this. ESP. 32. S. 3. Room. And text size. We can try. The 100. Like that. And we will call this. User. Switch. Image. And.

[0:47:07] Call this. I.O. Go. And. Then we will call. Programming. Interface. This will be. Power. Like that.

[0:47:59] This will be mounting. And. This will be. Quick. And. You can find. More information. If you go to. The spark phone. Believe. That it was. Spark phone. That invented. This. Standard. And they have. A lot of. Different boards. That you can. Interface to. So. Please go. And check out.

[0:48:44] The spark phone. Homepage. This will be. RGB. LED. And. We will call. This one. LDO. LDO. Like that. See. Are they. In the same height. Yep. Everything is fine. So now we have. Divided our small. Devices into some boxes here.

[0:49:30] It gives a much better overview of what we're doing. So now we should assign. Some of the pins here. To. The GPIO pins. And. As a default. I think that. SDA. And. SCL. They are. On. IO. 8. And. 9. So. We can. Move them up here. GPIO. 8. 9. Like that. And.

[0:50:15] Maybe. We should. Use the same. Length. We can move that out here. And. SCL. There. And we already have. Pull up resistors. On the. I2C pins. And here we have. GPIO 10. 11. 12. 13. 14.

[0:51:01] And 15. For our generic. Pinheader. And. We can just. Duplicate. And maybe. We can just. Duplicate all three. And just. Grab two. Like that. And. Yeah. We are not using. The USB lines. Maybe. We should just. Connect. A small test point. To them. So. We can say. Place. And. Let's. Find a test point. We'll take that.

[0:51:55] TEP1. And test point 2. And the LEDs. We can put them down here. On. GPIO. 38. Maybe. Yeah. Like that.

[0:52:50] And the user switch. We can put that on. The last down here. Duplicate. And. Like that. So. We also need to have. The TXD pins. For the powering connector. We have. I. I.O. Zero. We have. Enable. And we need to have. ESP. TXT. And. Rxd. And.

[0:53:42] We need to put them over here. TXT and Rxd. For the programming interface. That's. The TXD. Or. UART. Zero. Like that. So I think that we are very close to. Having finalized our schematic here. Just save it. So the next thing. That I normally do. Is to assign footprints. You have to assign the footprints.

[0:54:28] In the schematic editor. Before you start up the. PCB layout. Then you are sure. That you don't. By accident. Change the footprints. In the PCB editor. To something. That are not. Allowed. So it's much better. To do that here. In the. It's a very good idea. To do it here. In the schematic editor. And that's the way. To do it. And that. Can be done here. If you go to tools. And then go to. Edit symbols. Or. Edit symbol fields. You can of course. Just go into. Every component. And. Double click on it. And then you can assign a footprint. But then you have to go. And double click. Many times here. Instead. You can just go to. Edit symbol fields.

[0:55:14] And. Here you have a complete list. Of all the parts. That you have placed. On the schematic. And here you can assign. The footprints. So you can see. We are missing some. Assignments here. And so let's. Try and do that. So we see that. There's already. The references are. Already fill in. Of course. And the quantity. How. Of. How many we need. Of. All the parts. And the value of them. So now we're not. Just. We just need to. Fill in the footprints. So. Let's have a look. On the capacitors.

[0:56:00] Of course. And what we would like. So. 10. Micros. That can normally be. Like an 0603. That's the one. That I normally use. And. Now. KiCat. Just need to load. All the footprint libraries. And that just takes. A few seconds. To do. I think I need. A faster computer. But. Yeah. That's. On the. The wish list. Alright. So.

[0:56:47] We can. Find a capacitor here. And the. SMD capacitor. Capacitor. And. We need. An 0603. And for. The 100 nanos. I just. Use. An 0402. And for. The one micro. Yeah. Let's use. A. 0603. As well. And the. ESD diodes. Already filled in. Then we need. An LED. And I think. We'll go for. An. 0603. LED. See.

[0:57:35] LEDs. These. SMD. And. We can. You. It's easier. To solar. This one. Maybe. Let's just. Take. Take. Yeah. Let's take. This one. Mounting holes. That will be. A. Three millimeter. Mounting hole. Collapse. Everything. Mounting. Hole. Three point. Two millimeters. Just take.

[0:58:27] This. Standard one. Try this. And. Some. Pin headers. And. Collapse. Everything. Connector. Pin header. Two point. Four. Two point. Five. Four millimeters. Two. By. Three. Need a vertical one. That's one. And. A screw. Terminal.

[0:59:19] Terminal. Phoenix. And. Let's see. If we can. Find. The two. Pin one. One. Yeah. Let's try. This one. And. Then. We need. A quick connector. That's. A. JST connector. Connector. And. Then. We have. GST here.

[1:00:16] And. That's. An. SH. And. S. B. O. 4. B. I think. This is. This one. Oh. Sorry. KiCat. Just. Close down. By accident. Here. Let's try. Let's try. And get it. Up and running. Again. And let's.

[1:01:08] Let's not hope. That. We lost. Too much information. Too much information. Who's added symbol fields. Ah. So we have to. Assign some of the stuff again. I don't know what happened to. KiCat. It just shut down. It's very rare that I see that. So let's try again.

[1:01:59] 10 micro. And we need to load the libraries. Like that. And find some capacitors. S&D. And that was. 0603. Okay. 100 nanos. That was. That was. 0402. And we can just grab this one. Because this needs to be an.

[1:02:46] 0603. Green LED. LED. 0603. Mounting holes. 3.2 millimeters. And pin headers. Connector. Connector. Pin header. 2.54 millimeters. 2 by 3.

[1:03:32] Odd even. Pin. This is this one. And now we are added. There's also a 5 pin one here. 2 by 5. This one. And there we need the. Quick connector. And that was. The JST. SH. SMBO.

[1:04:23] For that one. And let's just say. Apply. Save schematic. And continue. Then we are sure. That it will not. Disappear again. So we will have. A. Screw tunnel. We can just collapse. And then find a terminal. That was Phoenix. PT. I think this is the one. Let's try it. Then we have some. Resistors. We will just use some. 0402 resistors. So resistors.

[1:05:17] SMD. 0402. And. We can just grab that one. Control. Control. C. Control. V. And now. We have two. Different buttons. And. I would like. One. The user. One. To be. Through hole. And. Switch. One. Is. The reset. One. One. So. We will find. An SMD type. For that one. And.

[1:06:05] Let's see. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. SV. If we can search for that, and 1000p, this is this one, and the other one, Tactical,

[1:07:12] is PST angled, 3, 1, yeah, this is this one, and a few test points, just use a round pad,

[1:08:09] and you can see here, the switches mixed values, two different ones, and there is no need to put mounting holes in the bill of materials, then you can just put a checkmark here, and if you don't want to have them assembled on the board, then you can check this one. But I'm quite confident that we have all the footprints defined now. Let's say apply, save, schematic, and continue. And here you can also make an export of the bill of materials.

[1:08:58] You see over here, there are some different columns, and you can also define your own. And let's say that you want to have, for example, the mouser part number, for example. Then you go over here, on the plus, and then you just write mouser. And then you see over here, we have the mouser column, and then you can just fill in the part number for these 10 micro capacitors and so forth down here. So when you generate the bill of materials, then you automatically get the mouser part numbers inserted there as well.

[1:09:49] Or that could also be all the information that you want to restore and be able to retrieve in a very nice manner. But yeah, this is a separate topic. You can export the bill of materials here, and you can decide here what you want to show actually. We don't want that mouser to be shown. So you can click it off here. So you can export the bill of materials and save that in a CSV file. And that has now been saved into our project, the CSV file.

[1:10:34] But before we will do that, we need one other thing. We want to save this, and we would like to go through all the designators, so that they are sorted in a nice manner, so it's easier to read the schematic and the design. So we will start here with C1 and C2, and we can do that very easily as well. You go to annotate schematic, and then you can decide in which direction you want to have it annotated. So we can go here in the Y position, or in the X position first, the entire schematic, and then we can say annotate, and close.

[1:11:25] Now we see here we have C1 and C2, and U1, and J1, and here you can see C3, and so forth. So you can see it's going down in this direction here. Here we have D1, we have R1 and R2, then we have R3, 4, 5, and we have 7 here, and 6 here. So you see it's going in this direction, we could also have it vertically here. But I think this is fine. So now we have assigned the designators, they are being sorted the way we want.

[1:12:16] And then let's go to edit symbol fields again, and then make a new export. OK. So now the designators, they are also fine in here. Enough of our bill of materials, and we can press OK. One other thing that is very nice, is that you can make a PDF file of your schematic. So you go to file, and you can go to plot, and here you can select different formats you want to plot it in. So PDF is already selected, and you have different options here.

[1:13:06] You can put it out in color or black and white. I would like this to be color. And we would like to plot the current page. Like that. Then we can go back to our projects. And over here we see that we have the CSV file, that's our bill of material. We have the PDF file here. Let's try and double click on that. And here we have a very nice schematic. So that's awesome features.

[1:13:53] But yeah, let's press save here. And now we are ready to start the design of the PCB. So I think we will take a short break here, and then let's get started doing the PCB design. See you soon. So now we are ready to start the PCB design, and we will go to tools, and then update PCB from schematic. That will automatically load all the defined footprints into our board. And I can just grab this window over here.

[1:14:40] Like that. And let's see, we don't have any errors. Update PCB. Close. Close. And here we have all the parts. And let's place that here on the board. So I would like to make a board that have the size of 45 by 45 millimeters. So let's go and switch to the edge cuts layer. That's where we have the board offline. And place a red angle here. And we can just move this a bit away.

[1:15:26] Then we can put the red angle here in the middle. And we are on a 1 by 1 millimeter grid. No, we are not on a 1 by 1 millimeter grid. So let's do that. 1 by 1 millimeter. And say 45 by 45 millimeter. Like that. And then we can start moving our parts in here. And the most important is of course the ESP 32S3 module.

[1:16:11] This looks to be in approximately the middle here. We need the power connector. Approximately there. Rotate the switch. User switch. Could have it around there. We have the programming connector. Just take the larger ones for now. Up there. And of course the mounting holes.

[1:16:59] Up there. And two last ones. So you just hover above the part. And press M for move. Like that. And the extension header. Could maybe place it around there. Move this down a bit. We have the LTO.

[1:17:53] We have the quick connector. Could be over here. Let's bring some of the smaller parts over. Like that. Like that. Like that. We have the user. Or the reset switch. Like that. Like that. Like that. We have an RGB LED.

[1:18:40] And the power LED. And the power LED. I think we will just fill in the necessary. Small things. We have the USB. We have the USB test pins here. We can just flip them to the other side. Like that. Move. And flip. Move.

[1:19:25] Move. And flip. Move. So they will be around there for now. And then we have the two capacitors. C1 and C2. Those are for the LTO. That's. One other thing you can do. Is to go to the schematic. And you can highlight the parts. Let's say we would like to have the parts.

[1:20:10] That are needed. Along with the user switch. Then we just highlight. Those three parts. Then we go to the PCB design. And you can see they are highlighted here. And you can press M for move. And then. We have all the three parts here. And then we can move them a bit together. Like that. And then we can move those. Down to. Switch down here. Where they are needed. And we have the 10 micro here. That's.

[1:20:55] Up here. For the decoupling. And we have one more. I think that was 100 nano here. We can check that. We can check that. This is the one. C5 and C6. And move. And move. Then we have. Those two connect. That's for the reset button. And we also need a resistor there. The pull up resistor.

[1:21:42] So let's highlight that one. That's R8. And R8 are here. Move these three parts together. And they need to be around here. Then we have some resistors for the LED. The RGB LED. Source free. Smooth. Like that. Then we have. And one cave resistor.

[1:22:28] I think that's the one for the LED. The power LED. And the remaining ones. R1. R2. R9. So we have one resistor up here. That's R9. That has to be on pin 15. And let's see where is that. It's right here. Let's place it there for now. And the two final resistors. They are 10K. And I see I forgot. In the schematic design.

[1:23:13] To change the value. Because they are not 10K value. Or 10K ohm. These are 2.2 kilo ohm. So I need to go in here. Change the values. 2K2. Okay. And 2K2. Okay. And 2K2. Okay. And I need to update the bill of material. And we can go to edit symbols. And let's say yeah. We have two 2.2 kilo ohm resistors. And then we export that. Okay. Apply it. Okay.

[1:23:58] And save. And then that should be fine. We can just do an update here. Like that. And move them to the right location. Save. And we can say update PCB from schematic again. And we see that these two values have changed. And close. And now we can see these are 2K2. And we can move these parts into our PCB as well.

[1:24:46] Like that. So now we have everything inside our defined board. So right now we have some square corners. I would like to have them rounded a bit. So you just double click here on the edge cut. And then you say shape modifications and fillet lines. 4 millimeters. And we can do. And we can do. Let's say. Let's try with. 3 millimeters. Yeah. It's not enough. Control Z. And we try again. And we say shape modification.

[1:25:37] Flat lines. 4 millimeters. Yeah. That looks much better. And right now we have the antenna outside the board. That's fine. Let's just have a look in the 3D viewer. If we are satisfied with the placement of the larger parts. Yeah. I think that's okay. Yeah. I think that's okay. That's okay for now.

[1:26:23] We can close this. Press save. So let's try and route some of the board. I would like this to be a 4 layer board. So we go into board setup. And here we can design or decide on the physical stack up. So we will assign this to be 4 layers. Like that.

[1:27:08] So we will route on the top and bottom layer. Then layer number 2 will be assigned to ground. And layer 3 to 3.3 walls. So for now we can just ignore the ground. Because that will be automatically connected. When we pour the top layer, bottom layer and the ground layer. And you see right now it's a bit confusing. Where we have all the text here. We can just click that away. I think that's fabrication output. We can just turn it off like that. And we would like the designators here for the mounting holes.

[1:27:57] We don't need them as well. Like that. So I think we could get started routing some of the parts here. And we will need a smaller grid. I think we will start with a 0.001 millimeter. That's fine. So let's start moving the parts here for the RGB LED. We should use a bit larger grid size.

[1:28:44] For this. Like that. Like that. We will move the designators and so on. When we have done the routing of the board. That's the last thing we'll do. This connector. We can move that down a bit.

[1:29:29] And if we want that silkscreen to be on the board. We can move it further in. But I think this is fine like this. And we can try and find the middle here. We can place. Some dimension lines. And we can just go to. Use a two layer. Place that. So we can either do it from here. The shape will automatically find the middle here. And what. We have. 37 millimeters over here.

[1:30:18] So the middle of that. That's 15. 3 and a half. 18 and a half millimeters. So the center. Is 18.5. And that should also be.

[1:31:03] 18.5 from the other one here. 18.5. So we can move this. And we know this is the middle. Like that. So we have the LED. Let's put the power LED down here. That's. Back that.

[1:31:48] Back that. And. We will just go directly into the LDO here. And. 5.5 volts. And. For a bit. And. The decoupling capacitor. And. And. And. And. There. And. And. And. And. And. And. And. And. one. On. On. The.

[1:32:33] Three. One. One. One. One. One. One. One. One. One. One. One. One. One. One. 3.3 volt layer with that directly we can put a VR on here and a VR on here

[1:33:27] and that's also 3.3 volts here and there so we have the signal coming in here from the user switch and the first thing you will see is the ESD diode let's route the signal down here and then we will have a capacitor to ground and a pull-up resistor

[1:34:21] like that via there and via there and this is automatically into a via or into the ground layer just move that out a bit like that and this will be also a 3.3 volt via and these will be connected we just need the signals to be routed so that's easy we can move this over a bit

[1:35:11] rotate this and route that into the MCU and connect that to 3.3 volts this is fine then we need the pull-up resistors on the quick connector we need the pull-up resistors on the quick connector something like this this this

[1:35:58] this this this this d for drag and we can have a via for 3.3 volts and a ground via like that and then we have the reset button here that's and we can just rotate that a bit so we have the ground out there and the signal inwards

[1:36:54] and the first thing we need to see is the ESD diode M for move and then the capacitor and then the capacitor and the pull-up resistor like that

[1:37:44] and then the ground via and power net via and we can also connect it in here like that programming header that's fine for now we have some of the decoupling for the room module and we need the 100 nano to be closest to the

[1:38:33] VCC pin here and drop the wires in there go to a 3.3 volt net there yes on the capacitors like that so i think we are ready to route some of the pins into the mcu let's see what we can do here that would be a 3.3 volt here

[1:39:21] and a ground via here for the LED yes so the user switch we will switch layer to the bottom layer and then we are so now this is connected

[1:40:10] great so let's see here on the auxiliary connector we can just place the usb pins here I'll not do anything about the impedance this time I'll just break them out like that

[1:41:09] drag move them a bit closer like that so let's see the io 11 where is that that's over here on this side so they are actually over here so I think we'll go on the bottom side and let's see drag

[1:41:55] down and you see when it there is a conflict it becomes highlighted with a green color so if we just move here in the middle then we are safe and we can place a view there move this up a bit and route from here

[1:42:41] place a view there perfect and let's continue here with the remaining ones place a view there i.o. 12 here there i.o. 15 so we need to go up there

[1:43:30] so we can change to top layer like that and then we have i.o. 14 so we need to go to the bottom layer and let's see if we have 3.3 volts coming in there that's fine so here we have the sda line

[1:44:20] so we can route that out here and maybe switch to the bottom layer and maybe switch to the bottom layer you could also choose to go through here so we can route that out here and that was sda then we have scl in here and we could just follow the other and we could just follow the other add square c line here and here we have the 3.3 volts for the pull up resistors

[1:45:10] and here we have the 3.3 volts for the pull up resistors and here we have the 3.3 volts for the pull up resistors then we have the LEDs RGB LEDs i think we need to go to the bottom layer here i can first check out what about the reset switch where is this line going I need to go up here to the programming connector, the txt line here, I can just go on the bottom

[1:45:58] layer to severe, like that rxd line, I can do that in a similar fashion like that, and then of course we need to go to the enable signal, on the sp32, you can just go behind here

[1:46:47] place a via there like that, underground 3.3 volts, that's fine, then we have I0, I think we need to go to the bottom layer here and we can just do it like this drag that could also go further up there like that let's save and let's see

[1:47:38] what else to have, we can concentrate on the LEDs now and we'll move to the top layer let's see I'll look it up there let's see and here

[1:48:29] like that and maybe we should move this in order to get a bit more room drag this a bit away like that like that like that like that and a via there and a via

[1:49:16] here and we're lucky that it just fits here and we're lucky that it just fits here there's a via that and then we have the final RGB LED pin so and maybe let's pin so via there and and then and and and here and and Something like that.

[1:50:23] And we have 3.3V of course to the RGB LED. Let me just check that we have all the signals routed. I think we are getting quite close. And I would like these tracks maybe to a bit be like 1mm there. And we could use this 0.6mm and 0.6mm.

[1:51:15] So we have the power lines are a bit thicker. And we could do that as well up here. And we could do that as well up here. 0.6mm. Leave this. All right. Now we could assign ground to the stack up.

[1:52:05] We can say place, draw, fill zones. And we will switch to a 1mm grid. Place, fill zones. And we will have on the top and on the inner 1 and the bottom layer. We would like to have 3.3V or sorry ground. Clearance should be 0.2mm.

[1:52:55] The thermal relief gap 0.2. And we could have the spoke width 0.3. Say OK. Then we define a square here where we want that to happen. All right. And then we can press B. Then we have fills, bottom layer with ground, top layer with ground and inner 1 with ground.

[1:53:43] We can just click off the different layers here. And then you can see that the inner 1 layer is a solid ground plane. And we can still see there are some missing wires here. That's the 3.3V layer. So we will assign 3.3V to the second inner layer. And then we should see most of these disappear. So we just say save again. And we can switch on the other layers. Make them visible again. Let's see. Place. Draw. Fill zones. Sorry. And then we need to be on the top layer.

[1:54:37] Place. Draw. Fill zones. And we want the 3.3V net. And we want that to be on the inner 2 layer. And we would like the same specifications. 0.2, 0.2 and 0.3 for the I spoke with. Then we do the same again. Then we are home again. And then we can say press B.

[1:55:25] And now you see that the 3.3V net is connected. And then we can turn off these again just to show it. And here we see the 3.3V layer. And there's the 3.3V VS. They are connected here. And of course the ground VS. They are not connected. So this looks fine. It seems that all the nets that we saw earlier they are now gone. And maybe I would like to delete these ones.

[1:56:13] If that's possible. I can keep them for now. Maybe this will give a problem later. Because they are very close to each other. Let's see if it gives problems. But we can enable all the layers again. And if you would like to see what goes on a bit more clear. In the different layers. Then we can say objects. And then we can say zones. And we can make them a bit more visible. Like this. And we can still see where the fills are. And maybe we should just move them up a bit still. And you see here.

[1:56:58] There are some areas where there's not too much fill. We can always insert some more ground VS. Then if you have areas that are not covered. And you would like that to happen. Then you can just insert some ground VS. And the way you do that is just go down here. Mark a via Ctrl D as a duplicate. And then let's try and put them in here. Let's go to a smaller grid. And Ctrl D. Like that. Ctrl D. Let's fill this. And then we press B. And then we will do a fill again.

[1:57:43] And then you see now this area has also been filled with copper. And there's also a small area here. But that's so very small. We can just have a look on the back side. And see if we are happy about the fill there. That also looks quite nice. There's just a bit of distance here between some of the lines. No problems. And we can press save. Alright. Now we can focus on the text and the designators.

[1:58:34] Sometimes I remove the designators for the smaller parts. But I think we have plenty of room here on this board. So we can just try and adjust it. And see how it looks. C4. I would like to rotate the text like this. And R8. Like that. And D4. Could have that here. Switch to. We can move that up here on the top. Like that. And R8. And R8. And R8. Like that. And D4. I can move that up here on top, like that.

[1:59:23] And here we have R1, R1 and J2. And you can go down here in the corner and say OK selection filter. We can say all items off and then we can just take the text. And when we then click here, it will only take the text and not all the other things. So it makes it a bit easier to navigate and select the right things that you want to have. So we can take R3 and R4.

[2:00:20] And R2, there. J1 and we can move this down to or this one up. C1 is fine. Because you can just try and avoid the vias. It will make the text a bit more visible then.

[2:01:06] R9, that's also OK. That's fine. C3 can be here. And R7, we can move that up a bit like that. And then we have the capacitors up here. And we can move this down a bit here.

[2:01:56] Alright. I think we could be happy about this. Maybe this would be nicer to have here. We can also put on a bit of text. I think there's a problem here. With this connector, it's a bit too far out. Then we need to just say selection filter all items. And then we can press move.

[2:02:57] Move this in a bit. Like that. Yeah. Perfect. We can place some text. Place. Draw text. And we would like to say this is our quick connector. And we want that to be on the silkscreen. And. Let's try with this. On 5.

[2:03:42] This is the quick connector. And this should be the reset connector. Let's move that down a bit. Let's move that down a bit. Like that. what else do we need use a switch

[2:04:39] and maybe we should write some labels here on the 3.3 volts and the pins for the expansion connector plus 3.3 volts and I think we need a smaller text here 0.75 and maybe

[2:05:31] this should be 0.1 so this would be a bit too close to the edge I think and let's select text and we can remove the plus I think that's fine and then we will have I O 10 and we can align it afterwards

[2:06:19] now we will just concentrate on the text and this is ground GND and then we can maybe just copy this to the other side ctrl D and let's tick designator for the module and put it up here put it up here this is 11 this is

[2:07:05] 13 and this is 15 15 and we could do the same on the programming header like that like that and we have ground there IO 0 then we have Rxd then we have Rxd

[2:07:51] Txd and Txd and enable like that like that and we could write move this text up here ESP32 ESP32 S3

[2:08:39] testboard testboard maybe something like that and we could place another text here place text we would need a plus sign on the plus side

[2:09:27] and the minus side sign sign like that and we could just write make made made by on like that and then I have a YouTube logo I think place

[2:10:13] footprint on YouTube let's see if there's room for it and sync that's fine and sync that's fine so let's move this down here maybe let's see how that looks let's

[2:10:59] let's move this down here maybe let's see how that looks we could just take this via down here let's just take this via down here let's see and I know vs interfering with our commercials here I think that's fine that's

[2:11:45] and then we need to align the text so if you select this and then we can say the spacing should be the same vertically and then we can say align we would like to have it centered and then we can say align and we would like to have it centered like that and they just touch the frame here so we can do the same for the other text

[2:12:31] so let's just take the text again here align distribute and then center again and then center again we can move that a bit in like that and we could just select this again and we could just select this again yep, perfect do that over here as well

[2:13:17] do that over here as well do that over here like that and finally and finally save

[2:14:09] all right then we can go to the back side and fill in some texts place I think there is also a symbol for Kika and we could flip that to the back side and we could say place text powered by

[2:14:55] by and and we would like that to be our sponsor channel sponsor pcbway.com dot com dot com and made by by by by by by by by by

[2:15:41] by by me by by it's just a mistake there dot dot right flip this to the back side And text selected. And then we have the problem with their test points and all that so we could

[2:16:30] just make it a bit smaller and see if that's possible to place. Something like that. And we can have a look in the 3D viewer.

[2:17:23] So the text looks fine. And we have maybe the logo should be just on the other side and we can also take that and put it a bit further away. So we need to grab also the footprints, move that a bit over here. And we could take this a bit further over there.

[2:18:11] Have a look again. I think that's fine. And you see we have a few missing 3D models. We can try and see if we can find those two missing. The RGB LED and the quick connector. Like that. Save. And one more thing you can see that there are some space here between the edge and the flood

[2:19:04] field there. We can also change that. Board setup. And design rules. And we can just change the cover to its clearance to 1.1 millimeter. And then you see now we are closer to the edge here. And this was this text, that's fine. And this was this text, that's fine. Like that. Like that. Or. Alright. I think we are done. Now we are closer to the edge here. Now we are closer to the edge here.

[2:19:50] with the layout. We are happy. And one of the final things for that is. We should do is to make a design rule check. And then verify that we don't have any routing errors. But yeah, firstly, let's try and find the 3D models, missing 3D models for the LED here.

[2:20:39] So we can check 3D models and I think I have a library here for those. So this is the RGB LED. Okay. And the quick connector. And this is this one. And we need to rotate it a bit. Like that.

[2:21:25] And it's a bit too high. feelin. And it's good. Don't곤 or throwing the dish out because you don't have a beautiful map. And it'll snap into this one. Again. And the frame's on the other. And once you pull out. Now, I'm going to save my headset's charger and plug in for it. If here, you actually have to drop the case. Let me drop. You can type... You can type that quickly and get the etume. And it's good. Again. I think there... I think about this mark program. You can publish it. geben a personal menu. And this's great information, the way I do want. Then the set direction. Came down a bit too much. Yeah.

[2:22:17] I think that's perfect. Save. We can just view this in the freedom model again. So now we have all the freedom models are there. And I'm not sure I'm not so happy about the. ESP32 room module. I think I have a better model of that. We can just try and verify. ESP32 is three.

[2:23:20] And then we can switch off the old one. And let's try and rotate it. Like that. It's a much better model. Yeah. And of course now it's highlighted. Like that. Then if we switch off. It's not highlighted anymore. Then we can save you again. And there we go.

[2:24:11] And maybe I will look a bit better if quick. I think this looks a bit messy. Maybe we'll take it down here. Like that. And like that. All right. Let's do the final check here. Inspect design wheel checks. To see if we have some issues with the port. Before we do the gerber files. And we see some errors here. So that's here around.

[2:25:00] It says that the hole size is out of range. So these holes are 0.2 millimeters. And we have a constraint that says. Okay. If we have holes that are smaller than 0.3 millimeters. Then we will throw an error. But this is fine. We can ignore that. Because when we upload the PCB to our manufacturer. They will make 0.2 millimeter holes. So we can live with that. So no big problems here on the board. Close. And now we should be ready to make our gerber data. And we say file.

[2:25:47] And we can just save our design now. And then we go to fabrication outputs. And we go to gerber. Then we have this window. And we will just. Verify that we have the four layers here. Paste layers. Silkscreen. And the solar mask. It's. And that's fine. So we will just define. Where we would like to. Store our gerber files. And we will just make a new folder here. Just call that gerber. Like that. And select it there. Choose folder. And yes. And then we say plot.

[2:26:37] And then we say generate files. Or drill files. Generate drill files. And generate. Close. So now we have our gerber files. Then we can zip them. And then upload them to our PCB manufacturer. We could also do the easy thing. I have installed here. A small plugin. For PCBWay. So if we just. Press this button. Then it will generate the. Necessary files. And upload those to. PCBWay automatically. Here we just have to. Specify. The layers. So that's just top.

[2:27:25] In a one. In a two. And then the bot. Submit. And then. Here we have all the. Specifications already in. Detected four layers board. 45 by 45 millimeters. We will have. There's one diff. One. Different design. Fr4. And you can. Select in between. Different colors. And. Different surface finishes. And then you can. Calculate the price. And up. And save it.

[2:28:11] To a card. And then order the PCBs. At PCBWay. But we will close this for now. And go to our design. And have a final look. And press save again. And. View. Video viewer. And here we have. The final design. I really hope. That you enjoyed. This small session. And you are ready. To try out. And make your own. Boards. So yeah. Good luck. And see you soon. And bye for now. Thank you.

[2:29:22] Bye. Bye. Bye. Bye. Bye. Bye. Bye. Bye. Bye. Bye. Bye. Bye.
