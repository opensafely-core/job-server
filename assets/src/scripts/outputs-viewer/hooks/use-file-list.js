import { useQuery } from "react-query";
import handleErrors from "../utils/fetch-handle-errors";

export default ({ apiUrl }) =>
  useQuery("FILE_LIST", async () =>
    fetch(apiUrl)
      .then(handleErrors)
      .then(async (response) => response.json())
  );
