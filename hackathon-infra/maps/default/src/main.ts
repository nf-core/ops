/// <reference types="@workadventure/iframe-api-typings" />

/**
 * nf-core Hackathon Map Script
 * 
 * This script provides interactive features for the hackathon map:
 * - Welcome message when entering the map
 * - Help zone popup with links to Slack, Docs, GitHub
 * - Social zone popup with links to Mastodon, Bluesky, YouTube, LinkedIn
 * - Hackathon info zone popup with links to Events, Projects, Guidelines
 * 
 * To add interactive zones to the map in Tiled:
 * 1. Create an Object Layer
 * 2. Draw a rectangle where you want the interaction
 * 3. Set the object's name property to match zone names below (e.g., 'needHelp')
 */

console.log('nf-core hackathon map script loaded');

let currentPopup: any = undefined;

function closePopup() {
    if (currentPopup !== undefined) {
        currentPopup.close();
        currentPopup = undefined;
    }
}

// Wait for the WA API to be ready
WA.onInit().then(() => {
    console.log('nf-core hackathon scripting API ready');
    
    // Welcome message
    WA.chat.sendChatMessage(
        'Welcome to the nf-core hackathon! Need help? Check out https://nf-co.re/events/2026/hackathon-march-2026',
        'nf-core bot'
    );

    // Help zone popup
    WA.room.area.onEnter('needHelp').subscribe(() => {
        currentPopup = WA.ui.openPopup('needHelpPopup', 'Need help with nf-core?', [
            {
                label: 'Slack',
                className: 'primary',
                callback: () => {
                    WA.nav.openTab('https://nf-co.re/join/slack');
                    closePopup();
                }
            },
            {
                label: 'Documentation',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://nf-co.re/docs');
                    closePopup();
                }
            },
            {
                label: 'GitHub',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://github.com/nf-core');
                    closePopup();
                }
            }
        ]);
    });
    WA.room.area.onLeave('needHelp').subscribe(closePopup);

    // Social/follow zone popup
    WA.room.area.onEnter('followUs').subscribe(() => {
        currentPopup = WA.ui.openPopup('followUsPopup', 'Connect with nf-core!', [
            {
                label: 'Mastodon',
                className: 'primary',
                callback: () => {
                    WA.nav.openTab('https://mstdn.science/@nf_core');
                    closePopup();
                }
            },
            {
                label: 'Bluesky',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://bsky.app/profile/nf-co.re');
                    closePopup();
                }
            },
            {
                label: 'YouTube',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://www.youtube.com/@nf-core');
                    closePopup();
                }
            },
            {
                label: 'LinkedIn',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://www.linkedin.com/company/nf-core');
                    closePopup();
                }
            }
        ]);
    });
    WA.room.area.onLeave('followUs').subscribe(closePopup);

    // Hackathon info zone popup
    WA.room.area.onEnter('hackathonInfo').subscribe(() => {
        currentPopup = WA.ui.openPopup('hackathonInfoPopup', 'Hackathon Resources', [
            {
                label: 'Event Info',
                className: 'primary',
                callback: () => {
                    WA.nav.openTab('https://nf-co.re/events/2026/hackathon-march-2026');
                    closePopup();
                }
            },
            {
                label: 'Projects',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://nf-co.re/events/2026/hackathon-march-2026#list-of-projects');
                    closePopup();
                }
            },
            {
                label: 'Code of Conduct',
                className: 'normal',
                callback: () => {
                    WA.nav.openTab('https://nf-co.re/code_of_conduct');
                    closePopup();
                }
            }
        ]);
    });
    WA.room.area.onLeave('hackathonInfo').subscribe(closePopup);

}).catch(e => console.error('Script init error:', e));

export {};
