request_headers = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "referer": "https://ocw.mit.edu/",
    "referrerPolicy": "strict-origin-when-cross-origin",
}

download_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def create_request_payload():
    return {
        "from": 0,
        "size": 200,
        "sort": [
            {"runs.best_start_date": {"order": "desc", "nested": {"path": "runs"}}}
        ],
        "post_filter": {
            "bool": {
                "must": [
                    {"bool": {"should": [{"term": {"object_type.keyword": "course"}}]}},
                    {"bool": {"should": [{"term": {"offered_by": "OCW"}}]}},
                    {
                        "bool": {
                            "should": [{"term": {"topics": "Mechanical Engineering"}}]
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"term": {"department_name": "Mechanical Engineering"}}
                            ]
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"term": {"course_feature_tags": "Lecture Notes"}},
                                {
                                    "term": {
                                        "course_feature_tags": "Problem Sets with Solutions"
                                    }
                                },
                                {"term": {"course_feature_tags": "Readings"}},
                            ]
                        }
                    },
                ]
            }
        },
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": {
                                "bool": {"must": [{"term": {"object_type": "course"}}]}
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "agg_filter_topics": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "bool": {
                                    "filter": {
                                        "bool": {
                                            "must": [
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "object_type.keyword": "course"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "offered_by": "OCW"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "department_name": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Lecture Notes"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Problem Sets with Solutions"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Readings"
                                                                }
                                                            },
                                                        ]
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "aggs": {"topics": {"terms": {"field": "topics", "size": 10000}}},
            },
            "agg_filter_department_name": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "bool": {
                                    "filter": {
                                        "bool": {
                                            "must": [
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "object_type.keyword": "course"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "offered_by": "OCW"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "topics": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Lecture Notes"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Problem Sets with Solutions"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Readings"
                                                                }
                                                            },
                                                        ]
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "department_name": {
                        "terms": {"field": "department_name", "size": 10000}
                    }
                },
            },
            "agg_filter_level": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "bool": {
                                    "filter": {
                                        "bool": {
                                            "must": [
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "object_type.keyword": "course"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "offered_by": "OCW"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "topics": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "department_name": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Lecture Notes"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Problem Sets with Solutions"
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "course_feature_tags": "Readings"
                                                                }
                                                            },
                                                        ]
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "level": {
                        "nested": {"path": "runs"},
                        "aggs": {
                            "level": {
                                "terms": {"field": "runs.level", "size": 10000},
                                "aggs": {"courses": {"reverse_nested": {}}},
                            }
                        },
                    }
                },
            },
            "agg_filter_course_feature_tags": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "bool": {
                                    "filter": {
                                        "bool": {
                                            "must": [
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "object_type.keyword": "course"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "offered_by": "OCW"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "topics": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "bool": {
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "department_name": "Mechanical Engineering"
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "course_feature_tags": {
                        "terms": {"field": "course_feature_tags", "size": 10000}
                    }
                },
            },
        },
    }
