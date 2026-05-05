import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createEventsSource } from "../../services/sse.js";
import { useUiStore } from "../../store/uiStore.js";

function mergeItemEvent(oldData, eventData) {
  if (!oldData?.jobs || eventData?.type !== "item_status") return oldData;
  return {
    ...oldData,
    jobs: oldData.jobs.map((job) => {
      if (job.id !== eventData.job_id) return job;
      return {
        ...job,
        status: eventData.job_status || job.status,
        items: (job.items || []).map((item) => (item.id === eventData.item_id ? { ...item, ...eventData } : item)),
      };
    }),
  };
}

export function useJobsEvents(enabled = true) {
  const queryClient = useQueryClient();
  const setSseStatus = useUiStore((state) => state.setSseStatus);

  useEffect(() => {
    if (!enabled) return undefined;

    const source = createEventsSource();
    setSseStatus("connecting");

    source.addEventListener("connected", () => setSseStatus("connected"));
    source.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);
        queryClient.setQueryData(["jobs"], (oldData) => mergeItemEvent(oldData, data));
      } catch {
        queryClient.invalidateQueries({ queryKey: ["jobs"] });
      }
    });
    source.onerror = () => {
      setSseStatus("reconnecting");
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    };

    return () => {
      source.close();
      setSseStatus("idle");
    };
  }, [enabled, queryClient, setSseStatus]);
}
