import { QueryClient } from "@tanstack/react-query";

export function createTaskQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        gcTime: 0,
        refetchOnWindowFocus: false
      }
    }
  });
}
