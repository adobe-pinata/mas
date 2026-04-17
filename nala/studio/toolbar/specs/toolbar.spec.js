export default {
    FeatureName: 'M@S Studio Toolbar',
    features: [
        {
            tcid: '0',
            name: '@studio-toolbar-sticky',
            path: '/studio.html',
            browserParams: '#page=content&path=nala',
            tags: '@mas-studio @toolbar @toolbar-sticky',
        },
        {
            tcid: '1',
            name: '@studio-toolbar-sticky-table',
            path: '/studio.html',
            browserParams: '#page=content&path=nala&render=table',
            tags: '@mas-studio @toolbar @toolbar-sticky',
        },
    ],
};
