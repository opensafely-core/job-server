import axios from "axios";
import { useQuery } from "react-query";

const getFileByUrl = async (fileUrl) => {
  const { data } = await axios.get(fileUrl);
  return data;
};

function useFile(fileUrl) {
  return useQuery(["file", fileUrl], () => getFileByUrl(fileUrl));
}

export default useFile;
