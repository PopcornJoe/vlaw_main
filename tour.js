// tour.js
console.log("tour.js loaded");
function runTour() {
    console.log("About to start Intro.js tour...");
    introJs().setOptions({
        steps: [
            { intro: "Hello from an external script!" },
            { intro: "No inline scripts needed." }
        ]
    }).start();
}
