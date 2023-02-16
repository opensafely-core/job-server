import { createContext, useContext } from "react";

const AppData = createContext({
  basePath: "",
  csrfToken: "",
  codelistGroups: [],
});

AppData.displayName = "AppData";

function useAppData() {
  const context = useContext(AppData);
  if (context === undefined) {
    throw new Error(
      "useAppData must be used within a AppData.Provider component"
    );
  }
  return context;
}

export { useAppData, AppData };
