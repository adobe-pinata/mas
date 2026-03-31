import { DOCS_GALLERY_PATH } from '../../utils/commerce.js';

export const FeatureName = 'Merch Lingo Cards Feature';
export const features = [
    {
        tcid: '0',
        name: '@MAS-Lingo-Product',
        path: DOCS_GALLERY_PATH.LINGO,
        data: {
            id: '', // FIXME(MWPW-186822): populate with Product fragment UUID
            title: '',
        },
        // @smoke @regression added once MWPW-186822 UUIDs are populated
        tags: '@mas-docs @mas-acom @mas-lingo-card @commerce',
    },
    {
        tcid: '1',
        name: '@MAS-Lingo-Special-Offers',
        path: DOCS_GALLERY_PATH.LINGO,
        data: {
            id: '', // FIXME(MWPW-186824): populate with Special Offers fragment UUID
            title: '',
        },
        // @smoke @regression added once MWPW-186824 UUIDs are populated
        tags: '@mas-docs @mas-acom @mas-lingo-card @commerce',
    },
    {
        tcid: '2',
        name: '@MAS-Lingo-Image',
        path: DOCS_GALLERY_PATH.LINGO,
        data: {
            id: '', // FIXME(MWPW-186817): populate with Image fragment UUID
            title: '',
        },
        // @smoke @regression added once MWPW-186817 UUIDs are populated
        tags: '@mas-docs @mas-acom @mas-lingo-card @commerce',
    },
    {
        tcid: '3',
        name: '@MAS-Lingo-Mini-Compare',
        path: DOCS_GALLERY_PATH.LINGO,
        data: {
            id: '', // FIXME(MWPW-186821): populate with Mini Compare fragment UUID
            title: '',
        },
        // @smoke @regression added once MWPW-186821 UUIDs are populated
        tags: '@mas-docs @mas-acom @mas-lingo-card @commerce',
    },
    {
        tcid: '4',
        name: '@MAS-Lingo-Segment',
        path: DOCS_GALLERY_PATH.LINGO,
        data: {
            id: '', // FIXME(MWPW-186818): populate with Segment fragment UUID
            title: '',
        },
        // @smoke @regression added once MWPW-186818 UUIDs are populated
        tags: '@mas-docs @mas-acom @mas-lingo-card @commerce',
    },
];
