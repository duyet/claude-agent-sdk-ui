'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/lib/store/chat-store';
import { AgentGrid } from '@/components/agent/agent-grid';
import { ChatContainer } from '@/components/chat-v2';
import { DashboardLayout } from '@/components/layout';
import { tokenService } from '@/lib/auth';
import { config } from '@/lib/config';
import { useAuth } from '@/components/providers/auth-provider';
import { useRouter, useParams } from 'next/navigation';

export default function HomePage() {
  const { isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const agentId = useChatStore((s) => s.agentId);
  const sessionId = useChatStore((s) => s.sessionId);
  const setSessionId = useChatStore((s) => s.setSessionId);
  const hasInitialized = useRef(false);
  const isUpdatingUrl = useRef(false);
  const lastProcessedSessionId = useRef<string | null>(null);

  // Initialize agentId from localStorage ONLY on first mount
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    // Initialize tokens for WebSocket (still needed)
    const initializeTokens = async () => {
      try {
        await tokenService.fetchTokens();
      } catch (err) {
        console.error('Failed to obtain JWT tokens:', err);
      }
    };
    initializeTokens();

    const savedAgentId = localStorage.getItem(config.storage.selectedAgent);
    if (savedAgentId && !useChatStore.getState().agentId) {
      useChatStore.getState().setAgentId(savedAgentId);
    }
  }, []);

  // Save agentId to localStorage when it changes (clear when null)
  useEffect(() => {
    if (agentId) {
      localStorage.setItem(config.storage.selectedAgent, agentId);
    } else {
      localStorage.removeItem(config.storage.selectedAgent);
    }
  }, [agentId]);

  // Sync session ID with URL
  useEffect(() => {
    // Don't update URL if we're currently processing a URL change
    if (isUpdatingUrl.current) return;

    // params.sessionId can be string | string[] | undefined
    // Convert to string | null
    const urlSessionId = typeof params.sessionId === 'string'
      ? params.sessionId
      : Array.isArray(params.sessionId)
        ? params.sessionId[0] || null
        : null;

    // Avoid processing the same session ID twice
    if (urlSessionId === lastProcessedSessionId.current) return;

    // If URL has a session ID different from current, load it
    if (urlSessionId && urlSessionId !== sessionId) {
      isUpdatingUrl.current = true;
      lastProcessedSessionId.current = urlSessionId;
      setSessionId(urlSessionId);
      // Reset flag after state update
      setTimeout(() => {
        isUpdatingUrl.current = false;
      }, 100);
    }
    // If session ID in store but not in URL, update URL
    else if (sessionId && sessionId !== urlSessionId) {
      isUpdatingUrl.current = true;
      lastProcessedSessionId.current = sessionId;
      router.push(`/s/${sessionId}`, { scroll: false });
      // Reset flag after navigation
      setTimeout(() => {
        isUpdatingUrl.current = false;
      }, 100);
    }
    // If session is cleared but URL has one, redirect to home
    else if (!sessionId && urlSessionId) {
      isUpdatingUrl.current = true;
      lastProcessedSessionId.current = null;
      router.push('/', { scroll: false });
      setTimeout(() => {
        isUpdatingUrl.current = false;
      }, 100);
    }
  }, [sessionId, params.sessionId, router, setSessionId]);

  // Show loading while auth is checking
  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <main className="flex flex-col flex-1 overflow-hidden">
        {!agentId ? <AgentGrid /> : <ChatContainer />}
      </main>
    </DashboardLayout>
  );
}
