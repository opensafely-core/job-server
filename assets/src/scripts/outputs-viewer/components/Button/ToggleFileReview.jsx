import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Button } from "react-bootstrap";
import useFileList from "../../hooks/use-file-list";
import useFileStore from "../../stores/use-file-store";

function ToggleFileReview() {
  // const { data: fileList } = useQuery(["FILE_LIST"]);
  // const { addCheckedFile, isFileChecked, removeCheckedFile } = useFileStore(
  //   (state) => state
  // );

  return (
    <Button
      className="mb-3"
      // onClick={() => toggleReviewState()}
      size="sm"
      variant="secondary"
    >
      Add all files to request
    </Button>
  );
}

export default ToggleFileReview;
