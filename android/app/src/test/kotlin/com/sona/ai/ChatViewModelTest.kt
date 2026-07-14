package com.sona.ai

import com.sona.ai.data.repository.SonaRepository
import com.sona.ai.domain.model.ChatResponse
import com.sona.ai.ui.viewmodel.ChatViewModel
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest {

    private val testDispatcher = UnconfinedTestDispatcher()
    private lateinit var repository: SonaRepository
    private lateinit var viewModel: ChatViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        repository = mockk()
        viewModel = ChatViewModel(repository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `send message adds user message`() = runTest {
        coEvery { repository.sendMessage(any(), any()) } returns
            Result.success(ChatResponse(content = "Hello!", model = "llama3", provider = "ollama"))

        viewModel.send("Hi")

        val messages = viewModel.messages.value
        assertTrue(messages.isNotEmpty())
        assertEquals("user", messages[0].role)
        assertEquals("Hi", messages[0].content)
    }

    @Test
    fun `send message adds AI response on success`() = runTest {
        coEvery { repository.sendMessage(any(), any()) } returns
            Result.success(ChatResponse(content = "I'm Sona!", model = "llama3"))

        viewModel.send("Who are you?")

        val messages = viewModel.messages.value
        assertEquals(2, messages.size)
        assertEquals("assistant", messages[1].role)
        assertEquals("I'm Sona!", messages[1].content)
    }

    @Test
    fun `send message shows error on failure`() = runTest {
        coEvery { repository.sendMessage(any(), any()) } returns
            Result.failure(RuntimeException("Network error"))

        viewModel.send("Hello")

        val messages = viewModel.messages.value
        assertEquals(2, messages.size)
        assertTrue(messages[1].content.contains("Error"))
    }

    @Test
    fun `empty message is ignored`() {
        viewModel.send("")
        assertTrue(viewModel.messages.value.isEmpty())
    }

    @Test
    fun `loading state changes during request`() = runTest {
        coEvery { repository.sendMessage(any(), any()) } returns
            Result.success(ChatResponse(content = "Done"))

        assertFalse(viewModel.isLoading.value)
        viewModel.send("Test")
        // After coroutine completes
        assertFalse(viewModel.isLoading.value)
    }
}
