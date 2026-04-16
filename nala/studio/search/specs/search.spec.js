export default {
    FeatureName: 'M@S Studio Search by Title',
    features: [
        {
            tcid: '0',
            name: '@studio-search-by-title-placeholder',
            path: '/studio.html',
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @search @search-by-title @search-by-title-smoke',
        },
        {
            tcid: '1',
            name: '@studio-search-by-title-exact-match',
            path: '/studio.html',
            data: {
                cardid: '8a338eba-55bf-4720-ab6d-79efd60177f6',
                query: 'card-with-locale-and-grouped-variations',
            },
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @search @search-by-title',
        },
        {
            tcid: '2',
            name: '@studio-search-by-title-partial-match',
            path: '/studio.html',
            data: {
                cardid: '8a338eba-55bf-4720-ab6d-79efd60177f6',
                query: 'card-with-locale',
            },
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @search @search-by-title',
        },
        {
            tcid: '3',
            name: '@studio-search-by-title-case-insensitive',
            path: '/studio.html',
            data: {
                cardid: '8a338eba-55bf-4720-ab6d-79efd60177f6',
                query: 'CARD-WITH-LOCALE',
            },
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @search @search-by-title',
        },
        {
            tcid: '4',
            name: '@studio-search-by-title-empty-query',
            path: '/studio.html',
            data: {
                query: 'card-with-locale',
            },
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @search @search-by-title',
        },
    ],
};
