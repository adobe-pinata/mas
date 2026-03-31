import { expect } from '@esm-bundle/chai';
import { AEM, filterByTags } from '../../src/aem/aem.js';

describe('aem.js', () => {
    const aem = new AEM('test');

    describe('filterByTags', () => {
        it('should filter tags with AND/OR logic', () => {
            const items = [
                {
                    id: 'item1',
                    tags: [{ id: 'mas:plan_type/abm' }, { id: 'mas:status/draft' }],
                },
                {
                    id: 'item2',
                    tags: [{ id: 'mas:plan_type/m2m' }, { id: 'mas:status/draft' }],
                },
                {
                    id: 'item3',
                    tags: [{ id: 'mas:plan_type/abm' }, { id: 'mas:plan_type/m2m' }],
                },
            ];

            // OR logic within same root
            const sameRootTags = ['mas:plan_type/abm', 'mas:plan_type/m2m'];
            const sameRootResult = items.filter(filterByTags(sameRootTags)).map((i) => i.id);
            expect(sameRootResult).to.deep.equal(['item1', 'item2', 'item3']);

            // AND logic between different roots
            const diffRootTags = ['mas:plan_type/abm', 'mas:status/draft'];
            const diffRootResult = items.filter(filterByTags(diffRootTags)).map((i) => i.id);
            expect(diffRootResult).to.deep.equal(['item1']);
        });
    });

    describe('method: searchFragment', () => {
        it('should fetch content fragments with multiple calls', async () => {
            window.fetch = async (url) => {
                if (url.includes('cursor1')) {
                    return {
                        ok: true,
                        json: async () => ({
                            items: [
                                {
                                    id: 2,
                                    fields: [{ name: 'variant', value: 'v2' }],
                                },
                            ],
                        }),
                    };
                } else {
                    return {
                        ok: true,
                        json: async () => ({
                            items: [
                                {
                                    id: 1,
                                    fields: [{ name: 'variant', value: 'v1' }],
                                },
                            ],
                            cursor: 'cursor1',
                        }),
                    };
                }
            };

            const result = await aem.searchFragment('some-query');

            const actual = [];

            for await (const items of result) {
                actual.push(...items);
            }

            expect(actual).to.deep.equal([
                { id: 1, fields: [{ name: 'variant', value: 'v1' }] },
                { id: 2, fields: [{ name: 'variant', value: 'v2' }] },
            ]);
        });
    });

    describe('method: searchFragment with title matching', () => {
        it('should include fragments matching by title when query is not UUID', async () => {
            const titleFragment = { id: 'title-frag-1', path: '/content/dam/title-match', title: 'CC Catalog Card' };

            window.fetch = async (url) => {
                // CF search endpoint returns no results
                if (url.includes('/search')) {
                    return {
                        ok: true,
                        json: async () => ({ items: [] }),
                    };
                }
                // querybuilder returns a path
                if (url.includes('querybuilder.json')) {
                    return {
                        ok: true,
                        json: async () => ({ hits: [{ path: '/content/dam/title-match' }] }),
                    };
                }
                // getFragmentByPath returns the title fragment
                if (url.includes('/cf/fragments')) {
                    return {
                        ok: true,
                        json: async () => ({ items: [titleFragment] }),
                    };
                }
                return { ok: false };
            };

            const actual = [];
            for await (const items of aem.searchFragment({ path: '/content/dam', query: 'CC Catalog' })) {
                actual.push(...items);
            }

            expect(actual).to.deep.equal([titleFragment]);
        });

        it('should not run title search when query is a UUID', async () => {
            let querybuilderCalled = false;
            const uuidQuery = '12345678-1234-1234-1234-123456789abc';

            window.fetch = async (url) => {
                if (url.includes('querybuilder.json')) {
                    querybuilderCalled = true;
                }
                return {
                    ok: true,
                    json: async () => ({ items: [], hits: [] }),
                };
            };

            // eslint-disable-next-line no-unused-vars
            for await (const items of aem.searchFragment({ path: '/content/dam', query: uuidQuery })) {
                // consume generator
            }

            expect(querybuilderCalled).to.equal(false);
        });

        it('should deduplicate fragments already returned by fullText search', async () => {
            const fragA = { id: 'frag-a', path: '/content/dam/path-a', title: 'Frag A' };
            const fragB = { id: 'frag-b', path: '/content/dam/path-b', title: 'Frag B' };

            window.fetch = async (url) => {
                // CF search returns fragA
                if (url.includes('/search')) {
                    return {
                        ok: true,
                        json: async () => ({ items: [fragA] }),
                    };
                }
                // querybuilder returns both paths (path-a overlaps, path-b is new)
                if (url.includes('querybuilder.json')) {
                    return {
                        ok: true,
                        json: async () => ({
                            hits: [
                                { path: '/content/dam/path-a' },
                                { path: '/content/dam/path-b' },
                            ],
                        }),
                    };
                }
                // getFragmentByPath for path-b returns fragB
                if (url.includes('path-b')) {
                    return {
                        ok: true,
                        json: async () => ({ items: [fragB] }),
                    };
                }
                return { ok: false };
            };

            const actual = [];
            for await (const items of aem.searchFragment({ path: '/content/dam', query: 'Frag' })) {
                actual.push(...items);
            }

            // fragA comes from fullText; only fragB should come from title search
            expect(actual).to.deep.equal([fragA, fragB]);
        });
    });

    describe('method: getFragmentTranslations', () => {
        it('should fetch translations', async () => {
            window.fetch = async () => ({
                ok: true,
                json: async () => ({ languageCopies: [] }),
            });

            const result = await aem.getFragmentTranslations('test-id');
            expect(result.languageCopies).to.be.an('array');
        });
    });
});
