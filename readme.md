# Squirrel Annoyer Widget Thingy
I have a few birdfeeders, and enjoy supporting the local bird population. The birds are polite, taking a seed or two and then fluttering away. Squirrels, however, have a tendency to hop on the feeder and sit there for an hour at a time just chompity-chomping away. They scare away all the birds and eat an unfair share. 

## The Journey So Far
I should have started documenting this earlier, but so far I've probably tried 50 different solutions to keep the squirrels off the feeders without setting traps or laying poison or anything else quite so drastic. I actually am fond of my furry friends, and simply wish to enforce good manners. 

I've tried all the feeders you've seen advertised on TV. They spin, they use springs to cover the inlets, they practically wash the dishes and make the bed. Alas, no luck via feeder variation. I next tried my own physical modifications. I've got the big inverted wok-style hat on one of the feeders now. Like the previous attempts, it worked well for a week or two but eventually an intrepid tree-rat figured out just the right bit of acrobatics to slide over the edge and catch the feeder below. 

I tried electrifying the fence. I managed to shock *myself* several times, but the squirrels escaped unscathed. It turns out it's harder than expected to electrify something hanging in the middle of the air. A real electrician would probably have had it working in 3 minutes, but alas...

I put barbed wire and razors between the feeders and where the squirrels come from. I felt kind of bad about it, until I watched them traipse past the traps with the grace of a Russian ballerina. 

I share a few of the highlights, but the journey had many more bumps and turns that I may write about later. 

## Fast-forward to Today
I've been enjoying dipping my toes into the hobby electronics world. I have Home Assistant set up and this has allowed me many opportunities to develop my tinkering abilities with cheap and affordable sensors and chips. I figured I might apply the same skills to my years-long battle against the small, grey nutty ninjas. 

I first set out to create a script that alerts me when a squirrel is on the feeder. You need a clear detection mechanism/trigger before anything else can be implemented. This logic is seen in `squirrel_annoyer.py`. I pull images from my cameras, and then use AI image processing to check for a squirrel. If we get a hit, an alarm sounds. Currently, the alarm is a rather alarming `scream.wav` I pulled from an copyright-free library online. My wife hates it. It scares the bajeesus out of me! But not just me...

## squirrel\_annoyer.py
After getting the basic script working I used it "manually". I'd hear the alarm and rush outside to scare the squirrels off the feeder. Funnily enough, it seemed some classical conditioning started to work. The squirrels would hear the scream and jump off the feeder on their own (at least sometimes). 

For some technical notes, I have a lot of troubleshooting messages in there, and it should be somewhat self-explanatory. I used AI to generate the skeleton and then tweaked it from there. 

In the future, I want to use my library of positive/negatively-identified photos to train my own local AI which will save me the outrageous $10/month it currently costs using OpenAI's 4o model. 

## code.py
Realizing there might be something to the sound angle of attack, I next bought an ESP32-C6 from Adafruit and started working on a speaker setup that I could power with a battery. My idea is to play an obnoxiously loud sound that's high enough to be above human thresholds so I don't annoy the neighbors (just their dogs). 

The current iteration uses an MQTT trigger (sent by the previously mentioned script) and plays the sound via an cheap attached tweeter speaker (designed for higher frequency work). I've got a Lithium Ion battery attached to keep it going, and basic testing has showed the 6600 mAh battery lasts over a day without any current power saving features enabled or utilized. As the squirrels only come out during daylight I can charge every night.

## Future Work
There's lots to do. I need to find a way to package up the speaker-widget and attach it to the speaker to take advantage of the inverse-square law and maximum amplitude/volume. This will need to be waterproof and fairly durable. Gee, I wish I had a 3D printer! 

Beyond that, I need to do some testing to get the right exact sound to play. The script on-device currently plays a short melody that I can hear for testing purposes, but eventually I don't want to hear it at all. 

I also need to train my own local image-detection model to save money on API calls. I plan to let the API run a while longer to build a really good library of yes/no's, and then it should be fairly quick work to my own model. 

And if all of this doesn't fit my final needs...then it's time to move on to attempt #52. Maybe a servo that bangs on the feeder? Pops a balloon full of water on the squirrel? Ideas are welcome.
