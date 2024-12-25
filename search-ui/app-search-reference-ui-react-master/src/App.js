import React from "react";

import ElasticsearchAPIConnector from "@elastic/search-ui-elasticsearch-connector";

import {
  ErrorBoundary,
  Facet,
  SearchProvider,
  SearchBox,
  Results,
  PagingInfo,
  ResultsPerPage,
  Paging,
  //Sorting,
  WithSearch
} from "@elastic/react-search-ui";
import { Layout } from "@elastic/react-search-ui-views";
import "@elastic/react-search-ui-views/lib/styles/styles.css";

/*
import {
  buildAutocompleteQueryConfig,
  buildFacetConfigFromConfig,
  buildSearchOptionsFromConfig,
  buildSortOptionsFromConfig,
  getConfig
  getFacetFields
} from "./config/config-helper";

const { hostIdentifier, searchKey, endpointBase, engineName } = getConfig();
*/

import secrets from "./config/engine.json";

const connector = new ElasticsearchAPIConnector({
  host: "http://52.77.217.6:9200",
  apiKey: secrets.searchKey,
  index: "cv-transcriptions"
});

const config = {
  searchQuery: {
    search_fields: {
      generated_text: {
        weight: 5,
        fuzziness: "AUTO"
      }
    },
    result_fields: {
      filename: {
        raw: {}
      },
      generated_text: {
        raw: {},
      },
      age: {
        raw: {}
      },
      duration: {
        raw: {}
      },
      gender: {
        raw: {}
      },
      accent: {
        raw: {}
      }
    },
    disjunctiveFacets: ["age", "gender", "accent","duration"],
    facets: {
      "age": {type:"value"},
      "gender": {type: "value"},
      "accent": {type: "value"},
      "duration": {
        type: "range",
        ranges: [
          {from: 0, to: 5, name:"0-5 sec"},
          {from: 5, to: 10, name:"5-10 sec"},
          {from: 10, to: 15, name:"10-15 sec"},
          {from: 15, to: 20, name:"15-20 sec"},
          {from: 20, to: 25, name:"20-25 sec"},
          {from: 25, to: 100, name:"25-100 sec"}
        ]
      }

    }
  },
  apiConnector: connector,
  alwaysSearchOnInitialLoad: true
};

export default function App() {
  return (
    <SearchProvider config={config}>
      <WithSearch mapContextToProps={({ wasSearched }) => ({ wasSearched })}>
        {({ wasSearched }) => {
          return (
            <div className="CV Transcriptions">
              <ErrorBoundary>
                <Layout
                  header={<SearchBox/>}
                  sideContent={
                    <div>
                      {wasSearched}
                      <Facet key={"1"} field={"age"} label={"age"} />
                      <Facet key={"2"} field={"gender"} label={"gender"} />
                      <Facet key={"3"} field={"accent"} label={"accent"} />
                      <Facet key={"4"} field={"duration"} label={"duration"} />
                    </div>
                  }
                  bodyContent={<Results 
                    shouldTrackClickThrough={true}
                    />
                  }
                  bodyHeader={
                    <React.Fragment>
                      {wasSearched && <PagingInfo />}
                      {wasSearched && <ResultsPerPage />}
                    </React.Fragment>
                  }
                  bodyFooter={<Paging />}
                />
              </ErrorBoundary>
            </div>
          );
        }}
      </WithSearch>
    </SearchProvider>
  );
}
