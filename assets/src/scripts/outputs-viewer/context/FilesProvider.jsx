import { PropTypes } from "prop-types";
import * as React from "react";

const FilesContext = React.createContext();

function filesReducer(state, action) {
  switch (action.type) {
    case "update": {
      return { ...state, ...action.state };
    }
    default: {
      throw new Error(`Unhandled action type: ${action.type}`);
    }
  }
}

function FilesProvider({ children, initialValue }) {
  const [state, dispatch] = React.useReducer(filesReducer, {
    authToken: "",
    basePath: "",
    csrfToken: "",
    filesUrl: "",
    prepareUrl: "",
    publishUrl: "",

    file: {
      name: "",
      url: "",
    },
    ...initialValue,
  });

  const value = { state, dispatch };
  return (
    <FilesContext.Provider value={value}>{children}</FilesContext.Provider>
  );
}

function useFiles() {
  const context = React.useContext(FilesContext);
  if (context === undefined) {
    throw new Error("useFiles must be used within a FilesProvider");
  }
  return context;
}

export { FilesProvider, useFiles };

FilesProvider.propTypes = {
  children: PropTypes.node.isRequired,
  initialValue: PropTypes.shape(),
};

FilesProvider.defaultProps = {
  initialValue: {},
};
