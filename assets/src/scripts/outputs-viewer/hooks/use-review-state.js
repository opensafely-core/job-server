import { useEffect, useState } from "react";

function useReviewState() {
  const [reviewState, setReviewState] = useState("view");
  const [isReviewEdit, setIsReviewEdit] = useState(false);
  const [isReviewView, setIsReviewView] = useState(true);

  useEffect(() => {
    if (reviewState === "view") {
      setIsReviewEdit(false);
      return setIsReviewView(true);
    }

    setIsReviewView(false);
    return setIsReviewEdit(true);
  }, [reviewState]);

  function toggleReviewState() {
    if (reviewState === "view") {
      return setReviewState("edit");
    }

    return setReviewState("view");
  }

  function setReviewView() {
    return setReviewState("view");
  }

  return {
    isReviewEdit,
    isReviewView,
    state: reviewState,
    toggleReviewState,
    setReviewView,
  };
}

export default useReviewState;
