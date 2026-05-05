import { useQuery } from "@tanstack/react-query";
import { getMe } from "./auth.api.js";

export function useMeQuery() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
    retry: false,
  });
}
