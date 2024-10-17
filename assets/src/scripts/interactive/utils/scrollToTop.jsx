import { useEffect } from "react";
import { useLocation } from "wouter";

export default function ScrollToTop() {
  const [pathname] = useLocation();

  // biome-ignore lint/correctness/useExhaustiveDependencies: ESLint to Biome legacy ignore
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}
